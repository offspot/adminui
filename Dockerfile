FROM alpine:3.22
LABEL org.opencontainers.image.source=https://github.com/offspot/adminui

COPY --from=ghcr.io/astral-sh/uv:0.9.9 /uv /uvx /bin/
RUN apk add --no-cache curl dumb-init yaml git
COPY pyproject.toml /src/
WORKDIR /src
RUN uv sync --no-install-project

ENV STATIC_DIR=/var/www/static
RUN \
    # FontAwesome font
    mkdir -p ${STATIC_DIR} \
    && curl -L -O https://use.fontawesome.com/releases/v7.1.0/fontawesome-free-7.1.0-web.zip \
        && unzip -o fontawesome-free-7.1.0-web.zip -d ${STATIC_DIR}/ \
        && rm -f fontawesome-free-7.1.0-web.zip \
    && curl -L -O https://github.com/twbs/bootstrap/releases/download/v5.3.8/bootstrap-5.3.8-dist.zip \
        && unzip -o bootstrap-5.3.8-dist.zip -d ${STATIC_DIR}/ \
        && rm -f bootstrap-5.3.8-dist.zip \
    && apk del curl \
    # WARN: this break apk but saves a lot of space
    # it's OK on prod but comment it during dev if you need packages
    && apk del apk-tools ca-certificates-bundle

ENV ADMIN_USERNAME=
ENV ADMIN_PASSWORD=
ENV SESSION_COOKIE_NAME=
ENV DEFAULT_SESSION_DURATION_MN=

COPY README.md main.py LICENSE /src/
COPY src /src/src/
RUN \
    ls -lh /src/src/adminui/static/ \
    && mv /src/src/adminui/static/*.js /src/src/adminui/static/branding ${STATIC_DIR}/ \
    && uv sync

EXPOSE 80
ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["/src/.venv/bin/fastapi", "run", "--host", "0.0.0.0", "--port", "80"]

