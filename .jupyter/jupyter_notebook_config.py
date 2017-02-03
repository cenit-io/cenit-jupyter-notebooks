try:
  import os
  import sys
  import json
  import traceback

  config_path = os.path.dirname(os.path.realpath(__file__))
  sys.path.insert(0, config_path)

  from cenitionotebook.services.contents.manager import ApiContentsManager

  c = get_config()

  ### Password protection ###
  # http://jupyter-notebook.readthedocs.io/en/latest/security.html
  c.NotebookApp.token = ''
  c.NotebookApp.password = ''

  ### CloudFoundry specific settings
  vcap_application_json = os.getenv('VCAP_APPLICATION', None)
  if vcap_application_json:
    vcap_application = json.loads(vcap_application_json)
    uri = vcap_application['uris'][0]
    c.NotebookApp.allow_origin = 'https://{}'.format(uri)
    c.NotebookApp.websocket_url = 'wss://{}:4443'.format(uri)

  ### Whether to open in a browser after starting.
  c.NotebookApp.open_browser = False

  ### The notebook manager class to use.
  c.NotebookApp.contents_manager_class = 'cenitionotebook.services.contents.manager.ApiContentsManager'

  ### The cenit-io api base url.
  c.ApiContentsManager.cenitio_api_base_url = os.getenv('CENITIO_API_BASE_URL', 'http://127.0.0.1:3000/api/v2')

except Exception:
  traceback.print_exc()
  # if an exception occues, notebook normally would get started
  # without password set. For security reasons, execution is stopped.
  exit(-1)
