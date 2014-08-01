FROM mozillamarketplace/centos-mysql-mkt:0.1

RUN mkdir -p /pip/{cache,build}
ADD requirements /pip/requirements
WORKDIR /pip
RUN pip install -b /pip/build --download-cache /pip/cache --no-deps -r /pip/requirements/dev.txt

EXPOSE 2602

CMD ["python", "src/manage.py", "runserver"]
