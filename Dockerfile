FROM node:18.12.0-alpine3.16 AS admin_web

WORKDIR /opt/vue-fastapi-admin
COPY /web ./web
RUN corepack enable && cd /opt/vue-fastapi-admin/web && pnpm install --frozen-lockfile && pnpm build


FROM node:20-alpine AS public_web

WORKDIR /opt/vue-fastapi-admin
COPY /frontend ./frontend
RUN corepack enable && cd /opt/vue-fastapi-admin/frontend && pnpm install --frozen-lockfile && pnpm build


FROM python:3.11-slim-bullseye

WORKDIR /opt/vue-fastapi-admin
ADD . .
COPY /deploy/entrypoint.sh .

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked,id=core-apt \
    --mount=type=cache,target=/var/lib/apt,sharing=locked,id=core-apt \
    sed -i "s@http://.*.debian.org@http://mirrors.ustc.edu.cn@g" /etc/apt/sources.list \
    && rm -f /etc/apt/apt.conf.d/docker-clean \
    && ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone \
    && apt-get update \
    && apt-get install -y --no-install-recommends gcc python3-dev bash nginx vim curl procps net-tools

RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY --from=admin_web /opt/vue-fastapi-admin/web/dist /opt/vue-fastapi-admin/web/dist
COPY --from=public_web /opt/vue-fastapi-admin/frontend/dist /opt/vue-fastapi-admin/frontend/dist
ADD /deploy/web.conf /etc/nginx/sites-available/web.conf
RUN rm -f /etc/nginx/sites-enabled/default \
    && ln -s /etc/nginx/sites-available/web.conf /etc/nginx/sites-enabled/ 

ENV LANG=zh_CN.UTF-8
EXPOSE 80

ENTRYPOINT [ "sh", "entrypoint.sh" ]