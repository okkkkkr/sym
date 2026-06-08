FROM node:20.20.2-bullseye AS admin_web

WORKDIR /opt/sym
COPY web/package.json web/pnpm-lock.yaml ./web/
RUN corepack enable && corepack prepare pnpm@9.15.9 --activate
RUN cd /opt/sym/web && pnpm install --frozen-lockfile
COPY web ./web
RUN cd /opt/sym/web && pnpm build


FROM node:20.20.2-bullseye AS public_web

WORKDIR /opt/sym
COPY official-web/package.json official-web/pnpm-lock.yaml ./official-web/
RUN corepack enable && corepack prepare pnpm@9.15.9 --activate
RUN cd /opt/sym/official-web && pnpm install --frozen-lockfile
COPY official-web ./official-web
RUN cd /opt/sym/official-web && pnpm build


FROM python:3.11-slim-bullseye AS app_runtime

WORKDIR /opt/sym

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked,id=core-apt \
    --mount=type=cache,target=/var/lib/apt,sharing=locked,id=core-apt \
    printf 'Acquire::Retries "10";\nAcquire::http::Timeout "60";\nAcquire::https::Timeout "60";\n' > /etc/apt/apt.conf.d/80-retries \
    && rm -f /etc/apt/apt.conf.d/docker-clean \
    && ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone \
    && apt-get update \
    && apt-get install -y --no-install-recommends gcc python3-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install -r requirements.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --extra-index-url https://pypi.org/simple \
    --default-timeout=300 \
    --retries 10

COPY app ./app
COPY migrations ./migrations
COPY run.py pyproject.toml ./
COPY scripts ./scripts

ENV LANG=zh_CN.UTF-8
EXPOSE 9999

CMD ["python", "/opt/sym/run.py"]


FROM nginx:1.27-alpine AS nginx_runtime

COPY --from=admin_web /opt/sym/web/dist /usr/share/nginx/html/admin
COPY --from=public_web /opt/sym/official-web/dist /usr/share/nginx/html/official
COPY deploy/docker/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
