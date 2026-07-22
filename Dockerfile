ARG WEB_VITE_PUBLIC_PATH=/
ARG WEB_VITE_BASE_API=/api/v1
ARG PUBLIC_VITE_API_BASE_URL=/api/v1

FROM node:20.20.2-bullseye AS admin_web

ARG WEB_VITE_PUBLIC_PATH
ARG WEB_VITE_BASE_API

WORKDIR /opt/sym
COPY web/package.json web/pnpm-lock.yaml ./web/
RUN corepack enable && corepack prepare pnpm@9.15.9 --activate
RUN cd /opt/sym/web && pnpm install --frozen-lockfile
COPY web ./web
RUN cd /opt/sym/web && VITE_PUBLIC_PATH="${WEB_VITE_PUBLIC_PATH}" VITE_BASE_API="${WEB_VITE_BASE_API}" pnpm build


FROM node:20.20.2-bullseye AS public_web

ARG PUBLIC_VITE_API_BASE_URL

WORKDIR /opt/sym
COPY official-web/package.json official-web/pnpm-lock.yaml ./official-web/
RUN corepack enable && corepack prepare pnpm@9.15.9 --activate
RUN cd /opt/sym/official-web && pnpm install --frozen-lockfile
COPY official-web ./official-web
RUN cd /opt/sym/official-web && VITE_API_BASE_URL="${PUBLIC_VITE_API_BASE_URL}" pnpm build


FROM python:3.11.11-slim-bullseye AS app_builder

WORKDIR /opt/sym

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked,id=core-apt \
    --mount=type=cache,target=/var/lib/apt,sharing=locked,id=core-apt \
    printf 'Acquire::Retries "10";\nAcquire::http::Timeout "60";\nAcquire::https::Timeout "60";\n' > /etc/apt/apt.conf.d/80-retries \
    && rm -f /etc/apt/apt.conf.d/docker-clean \
    && ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone \
    && apt-get update \
    && apt-get install -y --no-install-recommends gcc python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --prefix=/opt/python -r requirements.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --extra-index-url https://pypi.org/simple \
    --default-timeout=300 \
    --retries 10


FROM python:3.11.11-slim-bullseye AS app_runtime

WORKDIR /opt/sym

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked,id=runtime-apt \
    --mount=type=cache,target=/var/lib/apt,sharing=locked,id=runtime-apt \
    rm -f /etc/apt/apt.conf.d/docker-clean \
    && apt-get update \
    && apt-get install -y --no-install-recommends curl ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 sym \
    && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin sym \
    && mkdir -p /opt/sym/uploads /opt/sym/tmp /opt/sym/app/logs \
    && chown -R 10001:10001 /opt/sym

COPY --from=app_builder /opt/python /usr/local
COPY --chown=10001:10001 app ./app
COPY --chown=10001:10001 migrations ./migrations
COPY --chown=10001:10001 run.py pyproject.toml ./
COPY --chown=10001:10001 scripts ./scripts

ENV LANG=zh_CN.UTF-8
USER 10001:10001
EXPOSE 9999

CMD ["python", "/opt/sym/run.py"]


FROM nginx:1.27.3-alpine AS nginx_runtime

COPY --from=admin_web /opt/sym/web/dist /usr/share/nginx/html/admin
COPY --from=public_web /opt/sym/official-web/dist /usr/share/nginx/html/official
COPY deploy/docker/nginx.bootstrap.conf /etc/nginx/conf.d/default.conf
COPY deploy/docker/cloudflare-real-ip.inc /etc/nginx/cloudflare-real-ip.inc
COPY --chmod=0755 deploy/docker/40-admin-htpasswd.sh /docker-entrypoint.d/40-admin-htpasswd.sh

EXPOSE 80
