web: gunicorn quinielas_project.wsgi:application --bind 0.0.0.0:$PORT --workers 3
release: python manage.py migrate --settings=quinielas_project.settings_prod
