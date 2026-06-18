import ssl
from datetime import datetime

from app.models.admin import CertificateStatus
from app.settings import settings


CERTIFICATE_SPECS = (
    {
        "code": "main_site",
        "display_name": "主站 HTTPS 证书",
        "domain": "symluxlib.com",
        "path": lambda: str(settings.CERT_MONITOR_MAIN_CERT_PATH or "").strip(),
    },
    {
        "code": "static_site",
        "display_name": "静态域名证书",
        "domain": "static.symluxlib.com",
        "path": lambda: str(settings.CERT_MONITOR_STATIC_CERT_PATH or "").strip(),
    },
)

CERTIFICATE_STATUS_ERROR = "error"
CERTIFICATE_STATUS_EXPIRED = "expired"
CERTIFICATE_STATUS_WARNING = "warning"
CERTIFICATE_STATUS_VALID = "valid"


def _parse_certificate_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.strptime(value, "%b %d %H:%M:%S %Y %Z")
    if parsed.tzinfo is not None:
        return parsed.astimezone().replace(tzinfo=None)
    return parsed


def _build_status_payload(spec: dict, now: datetime) -> dict:
    cert_path = spec["path"]()
    payload = {
        "code": spec["code"],
        "display_name": spec["display_name"],
        "domain": spec["domain"],
        "cert_path": cert_path,
        "status": CERTIFICATE_STATUS_ERROR,
        "not_before": None,
        "not_after": None,
        "days_remaining": None,
        "last_checked_at": now,
        "last_error": "",
    }

    if not cert_path:
        payload["last_error"] = "未配置证书路径"
        return payload

    try:
        cert_info = ssl._ssl._test_decode_cert(cert_path)
        not_before = _parse_certificate_datetime(cert_info.get("notBefore"))
        not_after = _parse_certificate_datetime(cert_info.get("notAfter"))
    except FileNotFoundError:
        payload["last_error"] = "证书文件不存在"
        return payload
    except ssl.SSLError:
        payload["last_error"] = "证书内容异常"
        return payload
    except Exception as exc:
        payload["last_error"] = str(exc)[:500]
        return payload

    if not not_after:
        payload["last_error"] = "证书缺少过期时间"
        return payload

    remaining_seconds = (not_after - now).total_seconds()
    days_remaining = int(remaining_seconds // 86400)
    if remaining_seconds < 0:
        status = CERTIFICATE_STATUS_EXPIRED
    elif days_remaining <= max(0, int(settings.CERT_MONITOR_WARNING_DAYS)):
        status = CERTIFICATE_STATUS_WARNING
    else:
        status = CERTIFICATE_STATUS_VALID

    payload.update(
        {
            "status": status,
            "not_before": not_before,
            "not_after": not_after,
            "days_remaining": days_remaining,
            "last_error": "",
        }
    )
    return payload


class CertificateMonitorService:
    @staticmethod
    def serialize_status(status_obj: CertificateStatus | None) -> dict:
        if not status_obj:
            return {}

        return {
            "code": status_obj.code,
            "display_name": status_obj.display_name,
            "domain": status_obj.domain,
            "cert_path": status_obj.cert_path,
            "status": status_obj.status,
            "not_before": status_obj.not_before.strftime(settings.DATETIME_FORMAT) if status_obj.not_before else None,
            "not_after": status_obj.not_after.strftime(settings.DATETIME_FORMAT) if status_obj.not_after else None,
            "days_remaining": status_obj.days_remaining,
            "last_checked_at": status_obj.last_checked_at.strftime(settings.DATETIME_FORMAT) if status_obj.last_checked_at else None,
            "last_error": str(status_obj.last_error or "").strip(),
        }

    async def refresh_statuses(self) -> list[dict]:
        if not settings.CERT_MONITOR_ENABLED:
            return await self.list_statuses(auto_refresh_missing=False)
        now = datetime.now()
        results = []
        for spec in CERTIFICATE_SPECS:
            payload = _build_status_payload(spec, now)
            status_obj = await CertificateStatus.get_or_none(code=payload["code"])
            if status_obj:
                status_obj.update_from_dict(payload)
                await status_obj.save()
            else:
                status_obj = await CertificateStatus.create(**payload)
            results.append(self.serialize_status(status_obj))
        return results

    async def list_statuses(self, auto_refresh_missing: bool = False) -> list[dict]:
        status_map = {
            item.code: item
            for item in await CertificateStatus.all().order_by("id")
        }
        if settings.CERT_MONITOR_ENABLED and auto_refresh_missing and any(spec["code"] not in status_map for spec in CERTIFICATE_SPECS):
            return await self.refresh_statuses()

        results = []
        now = datetime.now()
        for spec in CERTIFICATE_SPECS:
            status_obj = status_map.get(spec["code"])
            if status_obj:
                results.append(self.serialize_status(status_obj))
                continue
            results.append(
                {
                    "code": spec["code"],
                    "display_name": spec["display_name"],
                    "domain": spec["domain"],
                    "cert_path": spec["path"](),
                    "status": CERTIFICATE_STATUS_ERROR,
                    "not_before": None,
                    "not_after": None,
                    "days_remaining": None,
                    "last_checked_at": now.strftime(settings.DATETIME_FORMAT),
                    "last_error": "尚未采集证书状态",
                }
            )
        return results


certificate_monitor_service = CertificateMonitorService()
