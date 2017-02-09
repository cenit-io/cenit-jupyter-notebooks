# cenit-jupyter-notebooks

Use this application to deploy Cenit-IO [Jupyter Notebook](https://jupyter.org/) to
heroku or CloudFoundry.

## Installation instructions

### Local installation

```
$ pip3 install notebook ipywidgets requests iso8601

$ gem install cztop
$ gem install iruby

$ git clone https://github.com/cenit-io/cenit-jupyter-notebooks.git
$ cd cenit-jupyter-notebooks
$ cp -ax .jupyter ~/

$ iruby notebook --debug
```

### heroku - manual deployment

Push this repository to your app or fork this repository on github and link your
repository to your heroku app.

```
$ git clone https://github.com/cenit-io/cenit-jupyter-notebooks.git
$ cd cenit-jupyter-notebooks

$ heroku apps:create <your_app>
$ heroku buildpacks:set https://github.com/pl31/heroku-buildpack-conda.git 
$ heroku buildpacks:set https://github.com/heroku/heroku-buildpack-ruby.git
```

### Environment variable

```
$ heroku config:set CENITIO_BASE_URL='http://cenit.io' -a <your_app>
```

## Environment variables

- `CENITIO_BASE_URL`: **(Used in Jupyter App)** Set Cenit-IO base url.
- `JUPYTER_NOTEBOOK_ARGS`: **(Used in Jupyter App)** Additional command line args passed to
  `jupyter notebook`; e.g. get a more verbose logging using `--debug`
- `JUPYTER_NOTEBOOKS_URL`: **(Used in Cenit-IO App)** Set jupyter app url.

