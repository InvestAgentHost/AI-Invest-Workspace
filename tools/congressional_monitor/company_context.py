"""Short, non-valuation company context for behavior reports.

The mapping is intentionally concise and sector-oriented.  It is used to
orient a reader, not to replace issuer filings or company research.
"""

from __future__ import annotations

import re
from typing import Any


COMPANY_CONTEXT: dict[str, dict[str, str]] = {
    "AAPL": {"name": "Apple", "sector": "消费电子与软件服务", "summary": "设计消费电子产品，并通过操作系统、应用商店和订阅服务获得收入。"},
    "AMAT": {"name": "Applied Materials", "sector": "半导体设备", "summary": "向晶圆厂和显示面板厂提供沉积、刻蚀、检测等制造设备。"},
    "AMD": {"name": "AMD", "sector": "半导体", "summary": "设计 CPU、GPU 和数据中心加速器，采用晶圆代工模式生产。"},
    "AMZN": {"name": "Amazon", "sector": "电商与云计算", "summary": "运营电商、广告和 AWS 云计算平台。"},
    "ANET": {"name": "Arista Networks", "sector": "数据中心网络", "summary": "提供面向云数据中心和大型企业的高速交换机与网络软件。"},
    "ASML": {"name": "ASML", "sector": "半导体设备", "summary": "提供先进光刻设备，是高端逻辑和存储芯片制造的关键设备供应商。"},
    "AVGO": {"name": "Broadcom", "sector": "半导体与基础设施软件", "summary": "提供网络、宽带、无线等芯片，并运营企业基础设施软件业务。"},
    "AXP": {"name": "American Express", "sector": "支付与信用卡", "summary": "运营支付网络、信用卡和面向消费者及企业的金融服务。"},
    "BAC": {"name": "Bank of America", "sector": "银行", "summary": "提供零售银行、商业银行、财富管理和投资银行服务。"},
    "BE": {"name": "Bloom Energy", "sector": "能源设备", "summary": "开发固体氧化物燃料电池和分布式发电系统，为企业客户提供现场电力。"},
    "BK": {"name": "BNY", "sector": "托管与资产服务", "summary": "为机构投资者提供资产托管、清算、基金服务和资产管理。"},
    "BLK": {"name": "BlackRock", "sector": "资产管理", "summary": "管理指数基金、ETF、主动基金和机构资产，并提供风险管理技术。"},
    "BRO": {"name": "Brown & Brown", "sector": "保险经纪", "summary": "为企业和个人提供财产、意外险及员工福利等保险经纪服务。"},
    "BWXT": {"name": "BWX Technologies", "sector": "核工业与国防", "summary": "为核电、海军核动力和政府项目提供核部件与技术服务。"},
    "CHRW": {"name": "C.H. Robinson", "sector": "物流服务", "summary": "运营第三方物流和货运经纪网络，连接货主与承运商。"},
    "CLH": {"name": "Clean Harbors", "sector": "环境服务", "summary": "处理危险废物并提供工业现场环境、回收和应急响应服务。"},
    "CPAY": {"name": "Corpay", "sector": "企业支付", "summary": "提供车队燃油卡、企业支付和跨境支付解决方案。"},
    "CRM": {"name": "Salesforce", "sector": "企业软件", "summary": "提供云端客户关系管理、营销、数据和生产力软件。"},
    "CRWD": {"name": "CrowdStrike", "sector": "网络安全", "summary": "通过云原生平台提供端点、身份和云工作负载安全服务。"},
    "ENTG": {"name": "Entegris", "sector": "半导体材料", "summary": "为芯片制造提供高纯材料、过滤、液体管理和污染控制产品。"},
    "FN": {"name": "Fabrinet", "sector": "光通信制造", "summary": "为光通信、激光和精密工业客户提供合同制造与封装服务。"},
    "FWONK": {"name": "Liberty Media Formula One", "sector": "体育媒体与赛事", "summary": "持有一级方程式赛车商业权益及相关媒体和赛事资产。"},
    "GEV": {"name": "GE Vernova", "sector": "能源设备", "summary": "提供燃气发电、风电、电网和电气化设备及服务。"},
    "GOOGN": {"name": "Alphabet 可转换优先证券", "sector": "特殊证券", "summary": "与 Alphabet 相关的强制可转换优先证券，不等同于普通股 GOOG/GOOGL。"},
    "GS": {"name": "Goldman Sachs", "sector": "投资银行与金融", "summary": "提供投资银行、证券交易、资产管理和财富管理服务。"},
    "HONAV": {"name": "Honeywell Aerospace", "sector": "航空航天", "summary": "为商用和军用航空提供发动机、航电、辅助动力和航空系统。"},
    "HUBB": {"name": "Hubbell", "sector": "电气与电网设备", "summary": "制造电气连接、配电、通信和电网基础设施产品。"},
    "INTC": {"name": "Intel", "sector": "半导体", "summary": "设计处理器和数据中心芯片，并建设晶圆制造与代工业务。"},
    "JPM": {"name": "JPMorgan Chase", "sector": "银行与金融", "summary": "运营消费与商业银行、投资银行、交易和资产管理业务。"},
    "LTH": {"name": "Life Time Group", "sector": "健身与健康服务", "summary": "运营综合健身俱乐部、运动场馆和相关健康生活服务。"},
    "LYV": {"name": "Live Nation Entertainment", "sector": "现场娱乐", "summary": "组织现场演出并运营票务平台和场馆。"},
    "META": {"name": "Meta Platforms", "sector": "社交媒体与数字广告", "summary": "运营 Facebook、Instagram 等平台，并投资虚拟现实和人工智能。"},
    "MKL": {"name": "Markel Group", "sector": "保险与投资", "summary": "以专业保险和再保险为核心，并持有多元化投资和运营资产。"},
    "MLM": {"name": "Martin Marietta Materials", "sector": "建筑材料", "summary": "生产骨料、沥青和混凝土等基础设施建设材料。"},
    "MSFT": {"name": "Microsoft", "sector": "软件与云计算", "summary": "提供 Windows、Office、Azure 云服务、企业软件和游戏业务。"},
    "MU": {"name": "Micron Technology", "sector": "存储器半导体", "summary": "生产 DRAM、NAND 和固态存储产品，服务数据中心、汽车和消费电子客户。"},
    "NFLX": {"name": "Netflix", "sector": "流媒体", "summary": "通过订阅和广告支持的服务发行影视内容。"},
    "NOW": {"name": "ServiceNow", "sector": "企业云软件", "summary": "提供 IT、员工和客户工作流自动化平台。"},
    "NVDA": {"name": "NVIDIA", "sector": "半导体与人工智能基础设施", "summary": "设计 GPU、网络和软件平台，服务人工智能、数据中心和专业计算。"},
    "PANW": {"name": "Palo Alto Networks", "sector": "网络安全", "summary": "提供网络、云、端点和安全运营平台及服务。"},
    "ROL": {"name": "Rollins", "sector": "服务业", "summary": "提供住宅和商业害虫防治服务。"},
    "SCI": {"name": "Service Corporation International", "sector": "殡葬服务", "summary": "运营殡仪馆、墓园和相关纪念服务。"},
    "SNDK": {"name": "SanDisk", "sector": "存储器半导体", "summary": "提供 NAND 闪存、固态硬盘和移动存储产品。"},
    "SPCX": {"name": "SpaceX 相关证券", "sector": "航天与卫星通信", "summary": "与 SpaceX 相关的非公开市场证券，涉及航天发射和卫星互联网业务；需特别核验证券属性。"},
    "STE": {"name": "STERIS", "sector": "医疗设备", "summary": "提供手术器械消毒、感染预防和医疗设备生命周期服务。"},
    "TDG": {"name": "TransDigm", "sector": "航空航天零部件", "summary": "设计和制造飞机高工程门槛零部件及售后产品。"},
    "TSCO": {"name": "Tractor Supply", "sector": "零售", "summary": "面向农村生活、农场和宠物需求运营专业零售门店及电商。"},
    "UBER": {"name": "Uber Technologies", "sector": "出行与配送平台", "summary": "运营网约车、外卖和货运平台。"},
    "UNH": {"name": "UnitedHealth Group", "sector": "健康保险与医疗服务", "summary": "提供商业和政府健康保险，以及医疗服务、药房和数据服务。"},
    "V": {"name": "Visa", "sector": "支付网络", "summary": "运营全球银行卡支付网络，通过交易处理和网络服务获得收入。"},
    "WAB": {"name": "Wabtec", "sector": "铁路设备", "summary": "为铁路货运和客运提供机车、制动、数字化和维护系统。"},
    "XOM": {"name": "Exxon Mobil", "sector": "综合能源", "summary": "从事上游油气、炼化、化工和低碳能源相关业务。"},
    "ZTS": {"name": "Zoetis", "sector": "动物健康", "summary": "研发和销售动物用药品、疫苗及诊断产品。"},
}


def _clean_issuer(issuer: Any, ticker: str) -> str:
    text = re.sub(r"\s+", " ", str(issuer or "")).strip()
    text = re.sub(r"\s*[-–—]\s*(?:Common Stock|Ordinary Shares|Class [A-Z] Common Stock).*$", "", text, flags=re.I)
    text = re.sub(r"\s*\([^)]*\)\s*$", "", text)
    return text or ticker


def company_context(ticker: str, issuer: Any = None) -> dict[str, str | bool]:
    """Return a concise context row, with an explicit fallback for unknowns."""

    key = str(ticker or "").strip().upper()
    known = COMPANY_CONTEXT.get(key)
    if known:
        return {"ticker": key, **known, "known": True}
    name = _clean_issuer(issuer, key)
    lowered = name.lower()
    heuristic_rules = (
        (("bank", "bancorp", "financial", "capital", "trust"), "银行与金融", "提供银行、金融或资产管理服务；具体业务需以公司公开资料核验。"),
        (("semiconductor", "microelectronics", "chip", "materials", "technolog", "software", "systems", "network", "cyber"), "科技与半导体", "名称显示其可能属于科技、软件、网络或半导体产业链；具体业务需进一步核验。"),
        (("energy", "electric", "power", "oil", "gas", "utility", "renewable"), "能源与公用事业", "名称显示其可能涉及能源、电力或公用事业；具体业务需进一步核验。"),
        (("pharma", "therapeutic", "biotech", "health", "medical", "laborator", "diagnostic"), "医疗健康", "名称显示其可能属于医药、医疗器械或健康服务；具体业务需进一步核验。"),
        (("insurance", "assurance"), "保险", "名称显示其可能属于保险或再保险；具体业务需进一步核验。"),
        (("aerospace", "aircraft", "aviation", "defense", "dynamics"), "航空航天与国防", "名称显示其可能涉及航空航天或国防产业链；具体业务需进一步核验。"),
        (("material", "cement", "steel", "mining", "chemical", "aggregate"), "原材料与建材", "名称显示其可能属于原材料、化工或建筑材料；具体业务需进一步核验。"),
        (("retail", "store", "supply", "market", "commerce"), "零售与消费", "名称显示其可能属于零售或消费服务；具体业务需进一步核验。"),
        (("media", "entertainment", "broadcast", "stream", "music"), "媒体与娱乐", "名称显示其可能属于媒体、内容或娱乐服务；具体业务需进一步核验。"),
        (("logistic", "freight", "transport", "shipping", "airline", "rail"), "运输与物流", "名称显示其可能属于运输、物流或供应链服务；具体业务需进一步核验。"),
        (("realty", "real estate", "property", "reit"), "房地产", "名称显示其可能属于房地产或 REIT；具体业务需进一步核验。"),
    )
    for keywords, sector, summary in heuristic_rules:
        if any(keyword in lowered for keyword in keywords):
            return {"ticker": key, "name": name, "sector": sector, "summary": summary, "known": False, "inferred": True}
    return {"ticker": key, "name": name, "sector": "未分类", "summary": "当前仅有申报中的发行人名称，需补充公司公开资料后再做业务判断。", "known": False}
