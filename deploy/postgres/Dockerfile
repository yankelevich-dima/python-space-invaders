FROM postgres:9.5

ENV POSTGRES_INITDB_ARGS "--data-checksums"
COPY init-user-db.sh /docker-entrypoint-initdb.d/
