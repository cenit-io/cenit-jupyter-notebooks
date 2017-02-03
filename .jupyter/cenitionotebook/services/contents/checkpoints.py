from tornado.web import HTTPError
from traitlets.config.configurable import LoggingConfigurable
from notebook.services.contents.checkpoints import Checkpoints


class Checkpoints(Checkpoints):
  """
  Base class for managing checkpoints for a ContentsManager.

  Subclasses are required to implement:

  create_checkpoint(self, contents_mgr, path)
  restore_checkpoint(self, contents_mgr, checkpoint_id, path)
  rename_checkpoint(self, checkpoint_id, old_path, new_path)
  delete_checkpoint(self, checkpoint_id, path)
  list_checkpoints(self, path)
  """

  def create_checkpoint(self, contents_mgr, path):
    """Create a checkpoint."""
    raise NotImplementedError('must be implemented in a subclass')

  def restore_checkpoint(self, contents_mgr, checkpoint_id, path):
    """Restore a checkpoint"""
    raise NotImplementedError('must be implemented in a subclass')

  def rename_checkpoint(self, checkpoint_id, old_path, new_path):
    """Rename a single checkpoint from old_path to new_path."""
    raise NotImplementedError('must be implemented in a subclass')

  def delete_checkpoint(self, checkpoint_id, path):
    """delete a checkpoint for a file"""
    raise NotImplementedError('must be implemented in a subclass')

  def list_checkpoints(self, path):
    """Return a list of checkpoints for a given file"""
    return []

  def rename_all_checkpoints(self, old_path, new_path):
    """Rename all checkpoints for old_path to new_path."""
    for cp in self.list_checkpoints(old_path):
      self.rename_checkpoint(cp['id'], old_path, new_path)

  def delete_all_checkpoints(self, path):
    """Delete all checkpoints for the given path."""
    for checkpoint in self.list_checkpoints(path):
      self.delete_checkpoint(checkpoint['id'], path)
