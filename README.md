# cenit-jupyter-notebooks

Use this application to deploy Cenit-IO [Jupyter Notebook](https://jupyter.org/) to
heroku or CloudFoundry.

## Installation instructions

### Local installation

```
$ pip3 install notebook ipywidgets requests iso8601

$ gem install ffi-rzmq
$ gem install cztop
$ gem install iruby

$ git clone https://github.com/cenit-io/cenit-jupyter-notebooks.git
$ cd cenit-jupyter-notebooks
$ cp -ax .jupyter ~/

$ jupyter notebook --debug
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
$ heroku buildpacks:set https://github.com/fabiokung/heroku-buildpack-fakesu.git

$ heroku run console

$ apt-get install libzmq-dbg libzmq-dev libzmq1
```

### Environment variable

```
$ heroku config:set CENITIO_BASE_URL='https://cenit.io' -a <your_app>
```

## Environment variables

- `CENITIO_BASE_URL`: **(Used in Jupyter App)** Set Cenit-IO base url. `//cenit.io`
- `JUPYTER_NOTEBOOK_ARGS`: **(Used in Jupyter App)** Additional command line args passed to `jupyter notebook`; e.g. get a more verbose logging using `--debug`
- `JUPYTER_NOTEBOOKS`: **(Used in Cenit-IO App)** Enable or disable notebooks in Cenit-IO. e.g. `True`
- `JUPYTER_NOTEBOOKS_URL`: **(Used in Cenit-IO App)** Set jupyter app url. e.g. `//cenit-jupyter-notebooks.herokuapp.com`

