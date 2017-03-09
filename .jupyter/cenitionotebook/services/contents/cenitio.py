from requests import Request, Session
from traitlets.config.configurable import LoggingConfigurable
from traitlets import Unicode
from datetime import datetime
from tornado import web
import nbformat
import iso8601
import json
import sys

NBFORMAT_VERSION = 4


class CenitIO(LoggingConfigurable):
  cenitio_api_base_url = Unicode(
    default_value='http://127.0.0.1:3000/api/v2',
    allow_none=False,
    config=True,
    help='The cenit-io base url.',
  )

  def cenit_io_send_request(self, uri, key, token, params={}, method='GET'):
    self.log.debug('CENIT-IO REQUEST: [%s] -> %s' % (method, uri))
    self.log.debug('CENIT-IO REQUEST PARAMS: %s' % (json.dumps(params)))

    try:
      options = {
        'headers': {'Content-Type': 'application/json'},
        'data': json.dumps(params)
      }
      if key != '-': options['headers']['X-User-Access-Key'] = key
      if token != '-': options['headers']['X-User-Access-Token'] = token

      session = Session()
      request = Request(method, uri, **options)
      prepped = request.prepare()
      response = session.send(prepped)

      self.log.debug('CENIT-IO RESPONSE: %s' % (response.text))

      data = json.loads(response.text)

    except:
      raise web.HTTPError(400, u'Cenit-IO error: %s' % sys.exc_info()[0])

    errors = data.get('errors')
    if errors: raise web.HTTPError(404, u'Cenit-IO error: %s' % errors)

    return data

  def cenit_io_all(self, path):
    key, token, path_without_tokens, parent, name = self.parse_notebook_path(path)

    uri = '%s/setup/notebook.json' % (self.cenitio_api_base_url)
    params = {
      'limit': 10000,
      'order': 'name',
      'parent': '"%s"' % path_without_tokens,
      'only': 'parent,name,type,writable,origin,created_at,updated_at',
    }
    data = self.cenit_io_send_request(uri, key, token, params)

    notebooks = data['notebooks']

    for (i, notebook) in enumerate(notebooks):
      notebooks[i] = self.parse(key, token, notebook)

    return notebooks

  def cenit_io_get(self, path, content=True):
    key, token, path_without_tokens, parent, name = self.parse_notebook_path(path)

    uri = '%s/setup/notebook.json' % (self.cenitio_api_base_url)
    params = {
      'limit': 1,
      'order': 'name',
      'parent': '"%s"' % parent,
      'name': name,
    }
    data = self.cenit_io_send_request(uri, key, token, params)

    if len(data['notebooks']) == 0: raise web.HTTPError(404, u'Notebook not found in path: %s' % path)

    return self.parse(key, token, data['notebooks'][0], content)

  def cenit_io_save(self, path, model, create=False):
    key, token, path_without_tokens, parent, name = self.parse_notebook_path(path)

    content = model.get('content', None)
    origin = model.get('origin', None)
    type = model.get('type', 'notebook')

    uri = '%s/setup/notebook.json' % (self.cenitio_api_base_url)
    params = {'name': name, 'parent': parent, 'type': type}

    if None != content: params['content'] = nbformat.writes(nbformat.from_dict(content), NBFORMAT_VERSION)
    if None != origin:  params['origin'] = origin
    if not create: params['id'] = model.get('id') or self.cenit_io_get(path).get('id')
    data = self.cenit_io_send_request(uri, key, token, params, 'POST')

    return self.parse(key, token, data['success']['notebook'])

  def cenit_io_delete(self, path):
    key, token, path_without_tokens, parent, name = self.parse_notebook_path(path)

    model = self.cenit_io_get(path, False)
    uri = '%s/setup/notebook/%s.json' % (self.cenitio_api_base_url, model.get('id'))
    self.cenit_io_send_request(uri, key, token, {}, 'DELETE')

  def parse(self, key, token, notebook, content=False):
    now = datetime.now()
    created_at = notebook.get('created_at', now)
    updated_at = notebook.get('updated_at', now)
    name = notebook.get('name', None)
    parent = notebook.get('parent', '')

    if type(created_at) == str:  created_at = iso8601.parse_date(created_at)
    if type(updated_at) == str:  updated_at = iso8601.parse_date(updated_at)

    model = {}
    model['id'] = notebook.get('id')
    model['last_modified'] = updated_at
    model['created'] = created_at
    model['mimetype'] = None

    model['name'] = name
    model['path'] = '%s/%s/%s/%s' % (key, token, parent, name)
    model['writable'] = notebook.get('writable', False)
    model['type'] = notebook.get('type', None)
    model['origin'] = notebook.get('origin', 'default')

    if content:
      model['format'] = 'json'
      if model['type'] == 'directory':
        model['content'] = self.cenit_io_all(model['path'])
      else:
        model['content'] = nbformat.reads(notebook.get('content', '{}'), NBFORMAT_VERSION)
    else:
      model['format'] = None
      model['content'] = None

    return model

  def parse_notebook_path(self, path):
    try:
      path_with_tokens = path.strip('/')
      key, token, path_without_tokens = ('%s/' % (path_with_tokens)).split('/', 2)
      path_without_tokens = path_without_tokens.strip('/')
      parent, name = ('/%s' % (path_without_tokens)).rsplit("/", 1)
      parent = parent.strip('/')
    except:
      raise web.HTTPError(404, u'Invalid notebook path: %s' % path)

    return (key, token, path_without_tokens, parent, name)
