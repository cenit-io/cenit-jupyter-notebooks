from requests import Request, Session
from traitlets import Unicode
from datetime import datetime
from tornado import web
import nbformat
import iso8601
import json
import sys

NBFORMAT_VERSION = 4


class CenitIO:
  cenitio_api_base_url = Unicode(
    default_value='http://127.0.0.1:3000/api/v2',
    allow_none=False,
    config=True,
    help='The cenit-io base url.',
  )

  def cenit_io_send_request(self, uri, key, token, params={}, method='GET'):
    try:
      options = {
        'headers': {
          'Content-Type': 'application/json',
          'X-User-Access-Key': key,
          'X-User-Access-Token': token
        },
        'data': json.dumps(params)
      }

      session = Session()
      request = Request(method, uri, **options)
      prepped = request.prepare()
      response = session.send(prepped)

      data = json.loads(response.text)

    except:
      raise web.HTTPError(400, u'Cenit-IO error: %s' % sys.exc_info()[0])

    error = data.get('error')
    if error: raise web.HTTPError(404, u'Cenit-IO error: %s' % error)

    return data

  def cenit_io_all(self, path):
    path = path.strip('/')

    try:
      (key, token, module) = path.split('/', 2)
    except:
      raise web.HTTPError(404, u'Invalid module path: %s' % path)

    uri = '%s/setup/notebook.json' % (self.cenitio_api_base_url)
    params = {'page': 1, 'limit': 100, 'order': 'name', 'module': module}

    data = self.cenit_io_send_request(uri, key, token, params)

    for (i, notebook) in enumerate(data['notebooks']):
      data['notebooks'][i] = self.parse(key, token, notebook)

    return data['notebooks']

  def cenit_io_get(self, path, content=True):
    path = path.strip('/')

    (key, token, module, name) = self.parse_notebook_path(path)

    uri = '%s/setup/notebook.json' % (self.cenitio_api_base_url)
    params = {'page': 1, 'limit': 1, 'order': 'name', 'module': module, 'name': name}

    data = self.cenit_io_send_request(uri, key, token, params)

    if len(data['notebooks']) == 0: raise web.HTTPError(404, u'Notebook not found in path: %s' % path)

    return self.parse(key, token, data['notebooks'][0], content)

  def cenit_io_save(self, path, model, create=False):
    path = path.strip('/')

    (key, token, module, name) = self.parse_notebook_path(path)

    nb = nbformat.from_dict(model['content'])
    uri = '%s/setup/notebook.json' % (self.cenitio_api_base_url)
    params = {
      'name': name,
      'module': module,
      'content': nbformat.writes(nb, NBFORMAT_VERSION)
    }

    if not create:
      params['id'] = model.get('id') or self.cenit_io_get(path).get('id')

    data = self.cenit_io_send_request(uri, key, token, params, 'POST')

    return self.parse(key, token, data['success']['notebook'])

  def cenit_io_delete(self, path):
    model = self.cenit_io_get(path)
    uri = '%s/setup/notebook/%s.json' % (self.cenitio_api_base_url, model.get('id'))
    (key, token, module, name) = self.parse_notebook_path(path)
    self.cenit_io_send_request(uri, key, token, {}, 'DELETE')

  def parse(self, key, token, notebook, content=False):
    now = datetime.now()
    created_at = notebook.get('created_at', now)
    updated_at = notebook.get('updated_at', now)

    if type(created_at) == str:  created_at = iso8601.parse_date(created_at)
    if type(updated_at) == str:  updated_at = iso8601.parse_date(updated_at)

    model = {}
    model['id'] = notebook.get('id')
    model['name'] = '%s' % (notebook.get('name'))
    model['path'] = '%s/%s/%s/%s' % (key, token, notebook.get('module'), notebook.get('name'))
    model['last_modified'] = updated_at
    model['created'] = created_at
    model['mimetype'] = None
    model['writable'] = True
    model['type'] = 'notebook'

    if content:
      model['format'] = 'json'
      model['content'] = nbformat.reads(notebook.get('content', '{}'), NBFORMAT_VERSION)
    else:
      model['format'] = None
      model['content'] = None

    return model

  def parse_notebook_path(self, path):
    try:
      (key, token, module) = path.split('/', 2)
      (module, name) = module.rsplit('/', 1)
    except:
      raise web.HTTPError(404, u'Invalid notebook path: %s' % path)

    return (key, token, module, name)
