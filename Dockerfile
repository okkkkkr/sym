FROM node:20.20.2-bullseye AS admin_web

WORKDIR /opt/sym
COPY /web ./web
RUN corepack enable && corepack prepare pnpm@9.15.9 --activate \
    && cd /opt/sym/web \
    && pnpm install --frozen-lockfile \
    && pnpm build


FROM node:20.20.2-bullseye AS public_web

WORKDIR /opt/sym
COPY /official-web ./official-web
RUN corepack enable && corepack prepare pnpm@9.15.9 --activate \
    && cd /opt/sym/official-web \
    && pnpm install --frozen-lockfile \
    && pnpm build


FROM python:3.11-slim-bullseye

WORKDIR /opt/sym
ADD . .
COPY /deploy/entrypoint.sh .

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked,id=core-apt \
    --mount=type=cache,target=/var/lib/apt,sharing=locked,id=core-apt \
    printf 'Acquire::Retries "10";\nAcquire::http::Timeout "60";\nAcquire::https::Timeout "60";\n' > /etc/apt/apt.conf.d/80-retries \
    && rm -f /etc/apt/apt.conf.d/docker-clean \
    && ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone \
    && apt-get update \
    && apt-get install -y --no-install-recommends gcc python3-dev bash nginx vim curl procps net-tools

RUN pip install -r requirements.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --extra-index-url https://pypi.org/simple \
    --default-timeout=300 \
    --retries 10

COPY --from=admin_web /opt/sym/web/dist /opt/sym/web/dist
COPY --from=public_web /opt/sym/official-web/dist /opt/sym/official-web/dist
ADD /deploy/web.conf /etc/nginx/sites-available/web.conf
RUN rm -f /etc/nginx/sites-enabled/default \
    && ln -s /etc/nginx/sites-available/web.conf /etc/nginx/sites-enabled/ 

ENV LANG=zh_CN.UTF-8
EXPOSE 80

ENTRYPOINT [ "sh", "entrypoint.sh" ]
