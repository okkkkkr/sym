const TIMEZONE_REGION_MAP = {
  'Asia/Shanghai': '中国大陆',
  'Asia/Urumqi': '中国大陆',
  'Asia/Hong_Kong': '中国香港',
  'Asia/Macau': '中国澳门',
  'Asia/Taipei': '中国台湾',
  'Asia/Tokyo': '日本',
  'Asia/Seoul': '韩国',
  'Asia/Singapore': '新加坡',
  'Asia/Kuala_Lumpur': '马来西亚',
  'Asia/Bangkok': '泰国',
  'Asia/Ho_Chi_Minh': '越南',
  'Asia/Manila': '菲律宾',
  'Asia/Jakarta': '印度尼西亚西部',
  'Asia/Makassar': '印度尼西亚中部',
  'Asia/Jayapura': '印度尼西亚东部',
  'Asia/Kolkata': '印度',
  'Asia/Dubai': '阿联酋',
  'Asia/Riyadh': '沙特阿拉伯',
  'Europe/Istanbul': '土耳其',
  'Europe/Moscow': '俄罗斯莫斯科地区',
  'Europe/London': '英国',
  'Europe/Paris': '法国',
  'Europe/Berlin': '德国',
  'Europe/Madrid': '西班牙',
  'Europe/Rome': '意大利',
  'Europe/Lisbon': '葡萄牙',
  'Australia/Sydney': '澳大利亚东部',
  'Australia/Melbourne': '澳大利亚东部',
  'Australia/Brisbane': '澳大利亚东部',
  'Australia/Adelaide': '澳大利亚中部',
  'Australia/Darwin': '澳大利亚中部',
  'Australia/Perth': '澳大利亚西部',
  'Pacific/Auckland': '新西兰',
  'America/New_York': '美国东部',
  'America/Detroit': '美国东部',
  'America/Chicago': '美国中部',
  'America/Denver': '美国山地',
  'America/Los_Angeles': '美国西部',
  'America/Anchorage': '美国阿拉斯加',
  'America/Toronto': '加拿大东部',
  'America/Vancouver': '加拿大西部',
  'America/Mexico_City': '墨西哥',
  'America/Sao_Paulo': '巴西',
  'America/Argentina/Buenos_Aires': '阿根廷',
  'Africa/Johannesburg': '南非',
  'Africa/Cairo': '埃及',
  'Africa/Lagos': '尼日利亚',
  'Etc/UTC': 'UTC 协调时间',
  UTC: 'UTC 协调时间',
}

const TIMEZONE_PREFIX_REGION_MAP = {
  'Asia/': '亚洲',
  'Europe/': '欧洲',
  'America/': '美洲',
  'Africa/': '非洲',
  'Australia/': '大洋洲',
  'Pacific/': '太平洋地区',
}

export function resolveTimezoneRegionLabel(timezone) {
  const normalizedTimezone = String(timezone || '').trim()
  if (!normalizedTimezone) {
    return '-'
  }

  if (TIMEZONE_REGION_MAP[normalizedTimezone]) {
    return TIMEZONE_REGION_MAP[normalizedTimezone]
  }

  const matchedPrefix = Object.keys(TIMEZONE_PREFIX_REGION_MAP).find((prefix) => normalizedTimezone.startsWith(prefix))
  if (matchedPrefix) {
    return TIMEZONE_PREFIX_REGION_MAP[matchedPrefix]
  }

  return '其他地区'
}