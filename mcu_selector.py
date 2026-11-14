import os
import streamlit as st
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "mcu_database.csv")

# ========== 登录 ==========
if "authed" not in st.session_state:
    st.session_state.authed = False

if not st.session_state.authed:
    st.title("🔧 MCU 选型工具 - 登录")
    pwd = st.text_input("请输入访问密码", type="password")
    try:
        correct = st.secrets["PASSWORD"]
    except Exception:
        correct = "123456"
    if pwd == correct:
        st.session_state.authed = True
        st.rerun()
    elif pwd:
        st.error("密码错误！")
    st.stop()

# ========== 加载数据库 ==========
@st.cache_data
def load_db(path):
    df = pd.read_csv(path)
    int_cols = ["flash_k","ram_k","gpio","freq_mhz","temp_max_c","uart","spi","i2c",
                "can","canfd","usb","eth","adc_ch","adc_bits","dac_ch","pwm_ch",
                "dma","rtc","iwdg","qspi","sdio","lcd_ctrl","crypto","trng"]
    for c in int_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
    df["price_cny"] = pd.to_numeric(df["price_cny"], errors="coerce").fillna(0.0)
    df["vcc_min"] = pd.to_numeric(df["vcc_min"], errors="coerce").fillna(0.0)
    df["vcc_max"] = pd.to_numeric(df["vcc_max"], errors="coerce").fillna(0.0)
    return df

df = load_db(CSV_PATH)

# 中文列名映射
CN = {
    "name":"型号","brand":"品牌","core":"内核","package":"封装",
    "flash_k":"Flash(KB)","ram_k":"RAM(KB)","gpio":"GPIO","freq_mhz":"主频MHz",
    "vcc_min":"Vmin","vcc_max":"Vmax","temp_max_c":"耐温℃",
    "uart":"UART","spi":"SPI","i2c":"I2C","can":"CAN","canfd":"CAN-FD",
    "usb":"USB","eth":"ETH","adc_ch":"ADC通道","adc_bits":"ADC位",
    "dac_ch":"DAC","pwm_ch":"PWM","dma":"DMA","rtc":"RTC","iwdg":"IWDG",
    "qspi":"QSPI","sdio":"SDIO","lcd_ctrl":"LCD","crypto":"加密","trng":"TRNG",
    "price_cny":"参考价元","supply":"供货","pin_compat":"pin兼容",
    "eco":"生态优点","con":"短板","datasheet_url":"资料链接",
    "score":"综合得分",
}

# 外设中文名 -> 列名
PERIPH_COL = {"CAN":"can","CAN-FD":"canfd","USB":"usb","ETH":"eth","DMA":"dma",
              "RTC":"rtc","IWDG":"iwdg","QSPI":"qspi","SDIO":"sdio",
              "LCD":"lcd_ctrl","加密":"crypto","TRNG":"trng"}
BOOL_PERIPH = list(PERIPH_COL.keys())

# ========== 应用场景预设 ==========
PRESETS = {
    "工业控制":   dict(gpio=40, flash=256, ram=64, freq=100, price=15, temp=105,
                     uart=3, spi=1, i2c=1, can=1, adc=8, dac=0, pwm=4,
                     must=["CAN","DMA","RTC","IWDG"]),
    "电机控制":   dict(gpio=20, flash=128, ram=32, freq=150, price=12, temp=105,
                     uart=2, spi=1, i2c=0, can=0, adc=6, dac=1, pwm=8,
                     must=["DMA","IWDG"]),
    "低功耗电池": dict(gpio=15, flash=64, ram=8, freq=24, price=5, temp=85,
                     uart=2, spi=1, i2c=1, can=0, adc=6, dac=0, pwm=4,
                     must=["RTC"]),
    "IoT/无线":  dict(gpio=15, flash=128, ram=64, freq=100, price=10, temp=85,
                     uart=2, spi=1, i2c=1, can=0, adc=4, dac=0, pwm=2,
                     must=["USB","TRNG"]),
    "数字电源":   dict(gpio=15, flash=128, ram=32, freq=150, price=12, temp=105,
                     uart=1, spi=1, i2c=0, can=0, adc=12, dac=2, pwm=8,
                     must=["DMA"]),
    "汽车电子":   dict(gpio=40, flash=256, ram=64, freq=100, price=25, temp=105,
                     uart=3, spi=1, i2c=1, can=1, adc=8, dac=0, pwm=4,
                     must=["CAN","CAN-FD","RTC","IWDG"]),
}

# 预设默认值，用 setdefault 不覆盖用户当前输入
DEFAULTS = {"gpio":30,"flash":64,"ram":10,"freq":72,"price":8.0,"temp":85,
            "uart":0,"spi":0,"i2c":0,"can":0,"adc":0,"dac":0,"pwm":0,
            "must_periph":["CAN","DMA","IWDG"]}
for _k,_v in DEFAULTS.items():
    st.session_state.setdefault(_k, _v)

# ========== 页面 ==========
st.set_page_config(page_title="MCU 选型工具", layout="wide")
st.title("🔧 嵌入式 MCU 选型工具")
st.caption(f"数据库共 {len(df)} 款芯片 · 国产为主 · 覆盖 Cortex-M0/M0+/M3/M4F/M7F 与 RISC-V / 电机 / 低功耗 / 无线")

tab_rec, tab_browse = st.tabs(["🎯 智能推荐", "📚 全库浏览"])

# ---------- 侧边栏需求 ----------
with st.sidebar:
    st.header("📌 应用场景预设")
    preset = st.selectbox("一键套用需求模板", ["（自定义）"] + list(PRESETS.keys()))
    if st.button("应用预设", type="primary"):
        if preset != "（自定义）":
            p = PRESETS[preset]
            for k,v in p.items():
                st.session_state[k] = v
            st.rerun()

    st.header("📐 资源 / 算力")
    st.number_input("最少 GPIO", min_value=0, key="gpio")
    st.number_input("最小 Flash(KB)", min_value=0, key="flash")
    st.number_input("最小 RAM(KB)", min_value=0, key="ram")
    st.number_input("最低主频(MHz)", min_value=0, key="freq")
    st.number_input("单颗预算上限(元)", min_value=0.0, step=0.1, key="price")
    st.number_input("耐温要求(℃)", min_value=70, max_value=125, key="temp")

    st.header("🔌 外设数量门槛（0=不限）")
    c1,c2 = st.columns(2)
    with c1:
        st.number_input("UART ≥", min_value=0, key="uart")
        st.number_input("SPI ≥", min_value=0, key="spi")
        st.number_input("I2C ≥", min_value=0, key="i2c")
        st.number_input("CAN ≥", min_value=0, key="can")
    with c2:
        st.number_input("ADC通道 ≥", min_value=0, key="adc")
        st.number_input("DAC ≥", min_value=0, key="dac")
        st.number_input("PWM ≥", min_value=0, key="pwm")

    st.header("✅ 必选外设（具备即可）")
    st.multiselect("必须包含", BOOL_PERIPH, key="must_periph")

    st.header("🏭 封装 / 品牌 / 供货")
    pkg_list = ["全部"] + sorted(df["package"].unique())
    package_filter = st.selectbox("封装筛选", pkg_list)
    brand_list = ["不限"] + sorted(df["brand"].unique())
    prefer_brand = st.selectbox("优先品牌", brand_list)
    prefer_stock = st.checkbox("优先现货充足", value=True)
    prefer_pin   = st.checkbox("加分：有 pin 兼容替代", value=True)

    st.markdown("---")
    if st.button("🔄 重载数据库"):
        st.cache_data.clear()
        st.rerun()

# 取当前需求值
gpio = st.session_state.gpio; flash = st.session_state.flash
ram = st.session_state.ram; freq = st.session_state.freq
max_price = st.session_state.price; temp_req = st.session_state.temp
nu = st.session_state.uart; ns = st.session_state.spi
ni = st.session_state.i2c; nc = st.session_state.can
nadc = st.session_state.adc; ndac = st.session_state.dac; npwm = st.session_state.pwm
must_periph = st.session_state.must_periph

# ---------- 打分 ----------
def score_mcu(row):
    s = 0.0
    # 价格（硬门槛）
    if max_price > 0:
        if row["price_cny"] > max_price:
            return -1
        s += (max_price - row["price_cny"]) / max_price * 25
    else:
        s += 15
    # 资源硬门槛
    if row["gpio"] < gpio: return -1
    s += 10
    if row["flash_k"] < flash: return -1
    s += 8
    if row["ram_k"] < ram: return -1
    s += 8
    if row["freq_mhz"] < freq: return -1
    s += 6
    # 温度硬门槛
    if row["temp_max_c"] < temp_req: return -1
    s += 5
    # 封装
    if package_filter != "全部" and row["package"] != package_filter:
        return -1
    # 数量门槛硬过滤
    if (row["uart"] < nu or row["spi"] < ns or row["i2c"] < ni or row["can"] < nc
            or row["adc_ch"] < nadc or row["dac_ch"] < ndac or row["pwm_ch"] < npwm):
        return -1
    s += 8
    # 必选外设硬过滤
    for m in must_periph:
        if row[PERIPH_COL[m]] < 1:
            return -1
    s += 15
    # 加分项
    if prefer_brand != "不限" and row["brand"] == prefer_brand:
        s += 5
    if prefer_stock:
        if row["supply"] == "现货充足":
            s += 4
        elif row["supply"] == "稳定":
            s += 2
    if prefer_pin and str(row["pin_compat"]) not in ("","无","nan"):
        s += 3
    return round(s, 2)

df_s = df.copy()
df_s["score"] = df_s.apply(score_mcu, axis=1)
matched = df_s[df_s["score"] >= 0].sort_values("score", ascending=False)

# ---------- 推荐页 ----------
with tab_rec:
    st.subheader("✅ 推荐结果")
    if len(matched) == 0:
        st.warning("没有满足全部硬性条件的芯片，请放宽条件：降低主频/Flash/RAM/外设门槛，或提高预算。")
    else:
        st.success(f"共 {len(matched)} 款满足条件，按综合得分排序（满分约 100）")
        show_cols = ["name","brand","core","package","flash_k","ram_k","gpio","freq_mhz",
                     "price_cny","score","supply","pin_compat","eco","con","datasheet_url"]
        disp = matched[show_cols].rename(columns=CN).copy()
        disp.insert(0, "排名", range(1, len(disp)+1))

        st.markdown("#### 🏆 Top 3")
        st.dataframe(disp.head(3), width="stretch", hide_index=True)
        st.markdown("#### 📋 全部匹配")
        st.dataframe(disp, width="stretch", hide_index=True)

        csv_out = matched[show_cols].rename(columns=CN).to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇️ 导出筛选结果 CSV", csv_out,
                           file_name="mcu_recommend.csv", mime="text/csv")

# ---------- 浏览页 ----------
with tab_browse:
    st.subheader("📚 芯片数据库浏览")
    kw = st.text_input("搜索（型号 / 品牌 / 内核 / 封装 / pin兼容）", "")
    b1,b2,b3 = st.columns(3)
    with b1: f_brand = st.selectbox("品牌", ["全部"]+sorted(df["brand"].unique()), key="bf")
    with b2: f_core  = st.selectbox("内核", ["全部"]+sorted(df["core"].unique()), key="bk")
    with b3: f_pkg   = st.selectbox("封装", ["全部"]+sorted(df["package"].unique()), key="bc")

    view = df.copy()
    if kw:
        view = view[view.apply(lambda r: kw.lower() in str(r.values).lower(), axis=1)]
    if f_brand != "全部": view = view[view["brand"] == f_brand]
    if f_core  != "全部": view = view[view["core"]  == f_core]
    if f_pkg   != "全部": view = view[view["package"] == f_pkg]

    st.caption(f"显示 {len(view)} / {len(df)} 款")
    st.dataframe(view.rename(columns=CN), width="stretch", hide_index=True)

    all_csv = df.rename(columns=CN).to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ 导出全库 CSV", all_csv, file_name="mcu_database_all.csv", mime="text/csv")

st.markdown("---")
st.caption("💡 价格为小批量参考价，量产以代理报价为准；维护数据库见 mcu_database.csv（编辑后点侧边栏「重载数据库」即可生效）")
