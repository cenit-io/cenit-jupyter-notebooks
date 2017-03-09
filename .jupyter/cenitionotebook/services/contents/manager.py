from notebook.services.contents.manager import ContentsManager
from nbformat.v4 import new_notebook
from .checkpoints import Checkpoints
from .cenitio import CenitIO
from tornado import web
import itertools
import datetime
import re

copy_pat = re.compile(r'\-Copy\d*\.')


class ApiContentsManager(ContentsManager, CenitIO):
  def _checkpoints_class_default(self):
    return Checkpoints

  def get(self, path, content=True, type=None, format=None):
    self.log.debug('GETTING FILE OR DIRECTORY:')
    self.log.debug('  PATH: %s' % (path))
    self.log.debug('  TYPE: %s' % (type))
    self.log.debug('  FORMAT: %s' % (format))
    self.log.debug('  CONTENT: %s' % (content))
    #################################################

    key, token, path_without_tokens, parent, name = self.parse_notebook_path(path)

    if name == '':
      model = {}
      model['name'] = 'home'
      model['path'] = ''
      model['last_modified'] = datetime.datetime.now()
      model['created'] = datetime.datetime.now()
      model['format'] = 'json'
      model['mimetype'] = None
      model['writable'] = False
      model['type'] = 'directory'
      model['content'] = self.cenit_io_all(path)
    else:
      model = self.cenit_io_get(path)

    if (content == False):
      model['content'] = None
      model['format'] = None

    return model

  def save(self, model, path, create=False):
    self.log.debug('SAVING: %s' % (path))
    #################################################
    return self.cenit_io_save(path, model, create)

  def delete_file(self, path):
    self.log.debug('DELETING FILE OR DIRECTORY: %s' % (path))
    #################################################
    self.cenit_io_delete(path)

  def rename_file(self, old_path, new_path):
    self.log.debug('RENAMING OLD FILE: %s' % (old_path))
    self.log.debug('RENAMING NEW FILE: %s' % (new_path))
    #################################################
    if new_path == old_path: return

    # Should we proceed with the move?
    if self.file_exists(new_path):
      raise web.HTTPError(409, u'File already exists: %s' % new_path.split('/', 2)[2])

    model = self.cenit_io_get(old_path)
    self.cenit_io_save(new_path, model)

  def file_exists(self, path):
    self.log.debug('CHECKING FILE EXISTENCE: %s' % (path))
    #################################################
    try:
      notebook = self.cenit_io_get(path, False)
      result = (notebook != None and notebook.get('type') != 'directory')
    except:
      result = False

    self.log.debug('CHECKING FILE EXISTENCE: %s [%s]' % (path, result))

    return result

  def dir_exists(self, path):
    self.log.debug('CHECKING DIRECTORY EXISTENCE: %s' % (path))
    #################################################
    try:
      notebook = self.cenit_io_get(path, False)
      result = (notebook != None and notebook.get('type') == 'directory')
    except:
      result = False

    self.log.debug('CHECKING DIRECTORY EXISTENCE: %s [%s]' % (path, result))

    return result

  def is_hidden(self, path):
    self.log.debug('CHECKING VISIBILITY: %s' % (path))
    #################################################
    # Assuming that all files or directories are visible.
    return False

  def new(self, model=None, path=''):
    self.log.debug('-----------------------------------------------------: %s' % (path))

    path = path.strip('/')

    if model is None: model = {}

    model.setdefault('type', 'notebook')
    model['content'] = new_notebook()
    model['format'] = 'json'

    model = self.save(model, path, True)

    return model

  def copy(self, from_path, to_path=None):
    self.log.debug('-----------------------------------')
    model = self.get(from_path)
    if model == None: raise web.HTTPError(404, u'Notebook not found in path: %s' % from_path)

    path = re.sub(r'.ipynb$', '', from_path.strip('/'))
    from_dir, from_name = path.rsplit('/', 1)
    to_path = to_path or from_dir

    for i in itertools.count():
      to_name = re.sub(r'-0$', '', '%s-copy-%s.ipynb' % (from_name, i))
      if not self.file_exists('%s/%s' % (to_path, to_name)): break

    to_path = '%s/%s' % (to_path, to_name)

    model.pop('id')
    model.pop('origin')
    model = self.save(model, to_path, True)

    return model
