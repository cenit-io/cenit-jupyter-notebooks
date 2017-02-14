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
        'headers': {'Content-Type': 'application/json'},
        'data': json.dumps(params)
      }
      if key != '-': options['headers']['X-User-Access-Key'] = key
      if token != '-': options['headers']['X-User-Access-Token'] = token

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
      key, token, module = ('%s/' % (path)).split('/', 2)
      module = module.strip('/')
    except:
      raise web.HTTPError(404, u'Invalid module path: %s' % path)

    uri = '%s/setup/notebook.json' % (self.cenitio_api_base_url)
    params = {'limit': 10000}

    self.log.debug('MODULE: [%s]' % (module))

    if module == '':
      params['order'] = 'module'
      params['only'] = 'module'
    else:
      params['order'] = 'name'
      params['module'] = module
      params['only'] = 'module,name,writable,shared,created_at,updated_at'

    data = self.cenit_io_send_request(uri, key, token, params)

    if module != '':
      notebooks = data['notebooks']
    else:
      exists = {}
      notebooks = []
      for (i, notebook) in enumerate(data['notebooks']):
        if not exists.get(notebook['module'], False):
          notebooks.append(notebook)
          exists[notebook['module']] = True

    for (i, notebook) in enumerate(notebooks):
      notebooks[i] = self.parse(key, token, notebook)

    return notebooks

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

    content = model.get('content', None)
    shared = model.get('shared', None)

    uri = '%s/setup/notebook.json' % (self.cenitio_api_base_url)
    params = {'name': name, 'module': module}

    if None != content: params['content'] = nbformat.writes(nbformat.from_dict(content), NBFORMAT_VERSION)
    if None != shared:  params['shared'] = shared
    if not create: params['id'] = model.get('id') or self.cenit_io_get(path).get('id')
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
    name = notebook.get('name', None)
    module = notebook.get('module', None)

    if type(created_at) == str:  created_at = iso8601.parse_date(created_at)
    if type(updated_at) == str:  updated_at = iso8601.parse_date(updated_at)

    model = {}
    model['id'] = notebook.get('id')
    model['last_modified'] = updated_at
    model['created'] = created_at
    model['mimetype'] = None

    if name:
      model['name'] = name
      model['path'] = '%s/%s/%s/%s' % (key, token, module, name)
      model['writable'] = notebook.get('writable', False)
      model['type'] = 'notebook'
      model['shared'] = notebook.get('shared', False)
    else:
      model['name'] = module
      model['path'] = '%s/%s/%s' % (key, token, module)
      model['writable'] = False
      model['type'] = 'directory'
      model['shared'] = False

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
