#!/bin/sh

# Set default values for environment variables
export SESSION_MANAGER_HOST=${SESSION_MANAGER_HOST:-session-manager}
export PYTHON_BACKEND_HOST=${PYTHON_BACKEND_HOST:-backend-python}
export JAVASCRIPT_BACKEND_HOST=${JAVASCRIPT_BACKEND_HOST:-backend-javascript}
export RUBY_BACKEND_HOST=${RUBY_BACKEND_HOST:-backend-ruby}
export PHP_BACKEND_HOST=${PHP_BACKEND_HOST:-backend-php}
export KOTLIN_BACKEND_HOST=${KOTLIN_BACKEND_HOST:-backend-kotlin}
export HASKELL_BACKEND_HOST=${HASKELL_BACKEND_HOST:-backend-haskell}
export BASH_BACKEND_HOST=${BASH_BACKEND_HOST:-backend-bash}
export BACKEND_PORT=${BACKEND_PORT:-8000}

# Generate nginx.conf from template
envsubst '${SESSION_MANAGER_HOST} ${PYTHON_BACKEND_HOST} ${JAVASCRIPT_BACKEND_HOST} ${RUBY_BACKEND_HOST} ${PHP_BACKEND_HOST} ${KOTLIN_BACKEND_HOST} ${HASKELL_BACKEND_HOST} ${BASH_BACKEND_HOST} ${BACKEND_PORT}' < /etc/nginx/conf.d/nginx.conf.template > /etc/nginx/conf.d/default.conf

# Start nginx
exec nginx -g "daemon off;"