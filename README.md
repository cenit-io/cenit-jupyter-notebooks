# cenit-jupyter-notebooks

Use this application to deploy Cenit-IO [Jupyter Notebook](https://jupyter.org/) to
heroku or CloudFoundry.

## Installation instructions

### heroku - manual deployment

Push this repository to your app or fork this repository on github and link your
repository to your heroku app.

Use the [heroku-buildpack-conda](https://github.com/pl31/heroku-buildpack-conda):
```
$ heroku buildpacks:set https://github.com/pl31/heroku-buildpack-conda.git -a <your_app>
$ heroku buildpacks:set https://github.com/pl31/heroku-buildpack-ruby.git -a <your_app>
```

### Environment variable

```
$ heroku config:set CENITIO_API_BASE_URL='http://cenit.io/api/v2' -a <your_app>
```

## Environment variables

- `CENITIO_API_BASE_URL`: Set Cenit-IO API base url.
- `JUPYTER_NOTEBOOK_ARGS`: Additional command line args passed to
  `jupyter notebook`; e.g. get a more verbose logging using `--debug`

## Python version

If you want to use a special python version, you should set it in your environment.yml:

```
name: root
dependencies:
  - python=2.7
  - ...
```
