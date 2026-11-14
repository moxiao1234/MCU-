import streamlit as st
import pandas as pd

# ========== 密码校验 ==========
if "authed" not in st.session_state:
    st.session_state.authed = False

if not st.session_state.authed:
    st.title("🔧 MCU 选型工具 - 登录")
    pwd_input = st.text_input("请输入访问密码", type="password")
    try:
        correct_pwd = st.secrets["PASSWORD"]
    except Exception:
        correct_pwd = "123456"

    if pwd_input == correct_pwd:
        st.session_state.authed = True
        st.rerun()
    elif pwd_input:
        st.error("密码错误！")
    st.stop()


# ========== MCU 芯片库 ==========
mcu_lib = [
    {
        "name": "APM32F103CBT6",
        "brand": "极海",
        "package": "LQFP48",
        "flash_k": 128,
        "ram_k": 20,
        "gpio": 37,
        "freq_mhz": 72,
        "periph": {"CAN": True, "USB": False, "ADC": 10, "UART": 5, "SPI": 2, "I2C": 2, "PWM": 16, "DMA": True, "RTC": True, "IWDG": True},
        "price": 5.2,
        "eco": "标准库/ HAL，兼容 STM32F103，上手简单，国产供货稳",
        "con": "无高速 USB，算力一般，适合工业低速控制"
    },
    {
        "name": "APM32F103RBT6",
        "brand": "极海",
        "package": "LQFP64",
        "flash_k": 128,
        "ram_k": 20,
        "gpio": 51,
        "freq_mhz": 72,
        "periph": {"CAN": True, "USB": False, "ADC": 16, "UART": 5, "SPI": 2, "I2C": 2, "PWM": 16, "DMA": True, "RTC": True, "IWDG": True},
        "price": 6.3,
        "eco": "和 CBT6 库完全一致，引脚更多，直接换型号即可",
        "con": "价格更高，同样无内置 USB"
    },
    {
        "name": "GD32F103CBT6",
        "brand": "兆易创新",
        "package": "LQFP48",
        "flash_k": 128,
        "ram_k": 20,
        "gpio": 37,
        "freq_mhz": 108,
        "periph": {"CAN": True, "USB": True, "ADC": 10, "UART": 5, "SPI": 2, "I2C": 2, "PWM": 16, "DMA": True, "RTC": True, "IWDG": True},
        "price": 4.8,
        "eco": "生态成熟，主频更高，自带 USB，国产老牌",
        "con": "版本多，注意区分修订版，部分批次供货波动"
    },
    {
        "name": "CH32F103C8T6",
        "brand": "沁恒",
        "package": "LQFP48",
        "flash_k": 64,
        "ram_k": 20,
        "gpio": 37,
        "freq_mhz": 72,
        "periph": {"CAN": True, "USB": True, "ADC": 10, "UART": 5, "SPI": 2, "I2C": 2, "PWM": 14, "DMA": True, "RTC": True, "IWDG": True},
        "price": 3.5,
        "eco": "价格很香，资料多，官方 SDK 简单好上手",
        "con": "Flash 只有 64K，大程序容易溢出"
    },
    {
        "name": "AT32F403ACGT7",
        "brand": "雅特力",
        "package": "LQFP64",
        "flash_k": 256,
        "ram_k": 64,
        "gpio": 50,
        "freq_mhz": 208,
        "periph": {"CAN": True, "USB": True, "ADC": 16, "UART": 8, "SPI": 3, "I2C": 2, "PWM": 24, "DMA": True, "RTC": True, "IWDG": True},
        "price": 8.5,
        "eco": "性能强，外设丰富，兼容 ST 生态，适合复杂项目",
        "con": "单价偏高，功耗相对大"
    },
    {
        "name": "STM32F103C8T6",
        "brand": "ST",
        "package": "LQFP48",
        "flash_k": 64,
        "ram_k": 20,
        "gpio": 37,
        "freq_mhz": 72,
        "periph": {"CAN": True, "USB": True, "ADC": 10, "UART": 5, "SPI": 2, "I2C": 2, "PWM": 14, "DMA": True, "RTC": True, "IWDG": True},
        "price": 7.2,
        "eco": "全球生态天花板，例程、教程海量",
        "con": "贵，容易缺货，进口货交期不稳定"
    }
]

# ========== 打分函数 ==========
def score_mcu(item, req):
    s = 0.0
    if item["price"] <= req["max_price"]:
        s += (req["max_price"] - item["price"]) / req["max_price"] * 25
    else:
        return -1

    if item["gpio"] >= req["need_gpio"]:
        s += 15
    else:
        return -1

    if item["flash_k"] >= req["flash"]:
        s += 10
    if item["ram_k"] >= req["ram"]:
        s += 10

    if item["freq_mhz"] >= req["freq"]:
        s += 8

    must_ok = True
    if req["need_can"] and not item["periph"]["CAN"]:
        must_ok = False
    if req["need_usb"] and not item["periph"]["USB"]:
        must_ok = False
    if req["need_dma"] and not item["periph"]["DMA"]:
        must_ok = False
    if req["need_rtc"] and not item["periph"]["RTC"]:
        must_ok = False
    if req["need_iwdg"] and not item["periph"]["IWDG"]:
        must_ok = False
    if not must_ok:
        return -1
    s += 20

    if req["package_filter"] != "全部" and item["package"] != req["package_filter"]:
        return -1

    if req["prefer_brand"] != "不限":
        if item["brand"] == req["prefer_brand"]:
            s += 12
    return round(s, 2)

# ========== 页面 UI ==========
st.set_page_config(page_title="MCU 选型工具", layout="wide")
st.title("🔧 嵌入式 MCU 选型小工具")
st.markdown("填入项目需求，自动打分推荐芯片，适合工业控制、CAN、采集类项目")

with st.sidebar:
    st.header("📌 项目需求")
    need_gpio = st.number_input("最少需要 GPIO 数量", min_value=5, value=30)
    flash = st.number_input("最小 Flash (KB)", min_value=16, value=64)
    ram = st.number_input("最小 RAM (KB)", min_value=5, value=10)
    freq = st.number_input("最低主频 (MHz)", min_value=8, value=72)
    max_price = st.number_input("单颗预算上限（元）", min_value=1.0, value=8.0, step=0.1)

    st.subheader("必选外设")
    need_can = st.checkbox("必须 CAN", value=True)
    need_usb = st.checkbox("必须 USB")
    need_dma = st.checkbox("必须 DMA", value=True)
    need_rtc = st.checkbox("必须 RTC")
    need_iwdg = st.checkbox("必须独立看门狗", value=True)

    st.subheader("封装 & 品牌偏好")
    pkg_list = ["全部"] + sorted({x["package"] for x in mcu_lib})
    package_filter = st.selectbox("封装筛选", pkg_list)
    brand_list = ["不限"] + sorted({x["brand"] for x in mcu_lib})
    prefer_brand = st.selectbox("优先品牌", brand_list, index=1)

req = {
    "need_gpio": need_gpio,
    "flash": flash,
    "ram": ram,
    "freq": freq,
    "max_price": max_price,
    "need_can": need_can,
    "need_usb": need_usb,
    "need_dma": need_dma,
    "need_rtc": need_rtc,
    "need_iwdg": need_iwdg,
    "package_filter": package_filter,
    "prefer_brand": prefer_brand
}

res_list = []
for chip in mcu_lib:
    sc = score_mcu(chip, req)
    if sc >= 0:
        res_list.append({
            "型号": chip["name"],
            "品牌": chip["brand"],
            "封装": chip["package"],
            "Flash(KB)": chip["flash_k"],
            "RAM(KB)": chip["ram_k"],
            "GPIO": chip["gpio"],
            "主频MHz": chip["freq_mhz"],
            "单价预估": chip["price"],
            "综合得分": sc,
            "优点": chip["eco"],
            "短板": chip["con"]
        })

res_list.sort(key=lambda x: x["综合得分"], reverse=True)
top = res_list[:3]

st.subheader("✅ Top3 推荐芯片")
if top:
    df = pd.DataFrame(top)
    st.dataframe(df, use_container_width=True)
else:
    st.warning("没有符合全部条件的芯片，请放宽条件！")

st.markdown("---")
st.markdown("💡 提示：数据库可以自己在代码里新增芯片；价格为市场参考价，批量会更低")
