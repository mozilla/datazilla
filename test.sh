#!/bin/sh

if [ -z $DJANGO_SETTINGS_MODULE ]; then
  export DJANGO_SETTINGS_MODULE="datazilla.settings.base"
fi

py.test --cov-report html --cov datazilla
