import streamlit as st
import pandas as pd
import folium
import os
import geopandas as gpd
import random
import datetime
import rasterio
import numpy as np
import matplotlib.pyplot as plt
from folium import raster_layers
import branca.colormap as cm
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
from shapely.geometry import Point
from geopy.geocoders import Nominatim


# 知识图谱与 AI 相关
from langchain_community.graphs import Neo4jGraph
from langchain_community.chains.graph_qa.cypher import GraphCypherQAChain
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from folium.plugins import MarkerCluster, HeatMap, Fullscreen

# ================= 1. 页面配置 =================
st.set_page_config(page_title="水生入侵生物综合平台", page_icon="🌊", layout="wide")

# ================= 2. 侧边栏与全局配置 =================
with st.sidebar:
    st.header("⚙️ 系统配置")
    openai_key = st.text_input("DeepSeek API Key", value="sk-123456789abcdef1234567890abcdef123", type="password")
    neo4j_pwd = st.text_input("Neo4j 密码", value="12345sss", type="password")

# 全局加载物种列表数据，供两个 Tab 共享
data_dir = "data/gbif_results"
species_names = []
if os.path.exists(data_dir):
    species_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    species_names = [f.replace(".csv", "") for f in species_files]
else:
    st.error("未找到数据目录 data/gbif_results")




# ================= 3. 核心功能函数 =================

@st.cache_resource
def load_china_map():
    """
    只在系统启动时从网络下载一次中国省界 GeoJSON 并全局缓存。
    使用 cache_resource 适合缓存这种不需要频繁变更的大型只读对象。
    """
    china_geojson_url = "https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json"
    china_map = gpd.read_file(china_geojson_url)

    # 空间优化：如果只是为了统计点位归属哪个省，可以适当简化边界多边形，
    # 容差设为 0.005 度，能极大加快 sjoin 的碰撞计算速度，且对宏观统计影响极小。
    china_map['geometry'] = china_map['geometry'].simplify(0.005)

    return china_map[['name', 'geometry']]


@st.cache_data
def get_standard_province_data(csv_path):
    """GIS 空间识别逻辑 - 加速版"""
    df = pd.read_csv(csv_path)

    # 1. 预处理：剔除没有经纬度的脏数据，防止几何转换报错
    df = df.dropna(subset=['lng', 'lat'])

    # 2. 向量化加速：使用 points_from_xy 替代原先的 for 循环 zip
    # 这一步在处理数万级数据时，速度提升非常明显
    geometry = gpd.points_from_xy(df['lng'], df['lat'])
    gdf_points = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")

    # 3. 读取本地已缓存的省界多边形
    china_map = load_china_map()

    # 4. 执行空间连接，GeoPandas 内部会自动利用 R-tree 空间索引加速判定
    joined = gpd.sjoin(gdf_points, china_map, how="left", predicate='within')

    # 5. 统计聚合
    prov_counts = joined['name'].value_counts().reset_index()
    prov_counts.columns = ['province_name', 'counts']

    return joined, prov_counts


@st.cache_resource
def get_graph_chain(api_key, db_password):
    """
    同步 app.py 的核心逻辑：手动注入 Schema + 深度提示词
    """
    os.environ["OPENAI_API_KEY"] = api_key
    os.environ["OPENAI_API_BASE"] = "https://api.deepseek.com"

    # 1. 连接数据库并禁用自动刷新 (避免 APOC 依赖)
    graph = Neo4jGraph(
        url="bolt://localhost:7687",
        username="neo4j",
        password=db_password,
        refresh_schema=False
    )

    # 2. 手动注入精确的 Schema 结构 (来自 app.py)
    graph.structured_schema = {
        "node_props": {
            "Species": [{"property": "name", "type": "STRING"}],
            "Taxonomy": [{"property": "name", "type": "STRING"}],
            "Location": [{"property": "name", "type": "STRING"}],
            "Impact": [{"property": "name", "type": "STRING"}],
            "Control": [{"property": "name", "type": "STRING"}]
        },
        "relationships": [
            {"start": "Species", "type": "HAS_ALIAS", "end": "Species"},
            {"start": "Species", "type": "BELONGS_TO", "end": "Taxonomy"},
            {"start": "Species", "type": "NATIVE_TO", "end": "Location"},
            {"start": "Species", "type": "INVADES", "end": "Location"},
            {"start": "Species", "type": "CAUSES", "end": "Impact"},
            {"start": "Species", "type": "SUPPRESSED_BY", "end": "Control"}
        ],
        "metadata": {}
    }

    # 3. 深度 Cypher 生成提示词 (来自 app.py)
    CYPHER_GENERATION_TEMPLATE = """
        任务：将用户问题转换为 Cypher 查询。
        Schema：{schema}
        说明：
        1. 模糊匹配使用 CONTAINS。
        2. 仅使用 Schema 中的关系。
        3. 只输出 Cypher。
        用户问题：{question}
        Cypher："""

    # 4. 深度回答提示词 (直接复用 app.py 的精简版)
    QA_TEMPLATE = """你是一个生物入侵领域的专家。基于以下数据库信息回答问题：\n{context}\n问题：{question}\n回答："""

    cypher_prompt = PromptTemplate(input_variables=["schema", "question"], template=CYPHER_GENERATION_TEMPLATE)
    qa_prompt = PromptTemplate(input_variables=["context", "question"], template=QA_TEMPLATE)

    llm = ChatOpenAI(model="deepseek-chat", temperature=0)

    return GraphCypherQAChain.from_llm(
        llm=llm,
        graph=graph,
        verbose=True,
        validate_cypher=True,
        allow_dangerous_requests=True,
        cypher_prompt=cypher_prompt,
        qa_prompt=qa_prompt,
        return_intermediate_steps=True  # [关键] 必须添加此参数才能在返回结果中包含 Cypher
    )

# ================= 4. 界面主体 =================
tab1, tab2, tab3 = st.tabs(["🌍 分布识别分析", "🤖 智能知识问答", "📝 数据上报与更新"])

# --- Tab 1: 地理空间分析 ---
with tab1:
    if species_names:
        selected_species = st.selectbox("选择地图分析物种", species_names, key="map_species")
        csv_path = os.path.join(data_dir, f"{selected_species}.csv")

        with st.spinner('地理空间分析中...'):
            df_with_prov, province_stats = get_standard_province_data(csv_path)

        valid_coords = df_with_prov.dropna(subset=['lat', 'lng'])
        if not valid_coords.empty:
            center_lat = valid_coords['lat'].mean()
            center_lng = valid_coords['lng'].mean()
        else:
            center_lat, center_lng = 35.0, 105.0

        # --- UI 优化：将地图控件移至此处并横向排列 ---
        st.subheader("🗺️ 空间分布可视化")

        ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([2, 1, 1])
        with ctrl_col1:
            # 增加一个无聚合散点图选项，将原来的改名为聚合分布点图
            geo_mode = st.radio("数据可视化模式",
                                ["省级填色图", "聚合分布点图", "无聚合散点图", "空间热力图", "MaxEnt 适生区预测"],
                                horizontal=True)
        with ctrl_col2:
            basemap_style = st.selectbox("底图样式", ["卫星影像 (Esri)", "街道图 (OSM)"], label_visibility="collapsed")
        with ctrl_col3:
            st.metric(label="有效坐标记录数", value=f"{len(valid_coords)} 条")

        tiles_dict = {
            "街道图 (OSM)": "OpenStreetMap",
            "卫星影像 (Esri)": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        }
        attr_dict = {
            "卫星影像 (Esri)": "Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community"
        }

        # 1. 恢复完全默认的地图初始化
        m = folium.Map(
            location=[center_lat, center_lng],
            zoom_start=5,
            tiles=tiles_dict[basemap_style],
            attr=attr_dict.get(basemap_style, "")
        )

        # 2. 恢复默认全屏控件（会自动排在左上角缩放按钮下方）
        Fullscreen(title='全屏', title_cancel='退出').add_to(m)

        # 3. 图层渲染逻辑
        if geo_mode == "省级填色图":
            folium.Choropleth(
                geo_data="https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json",
                data=province_stats, columns=["province_name", "counts"],
                key_on="feature.properties.name", fill_color="YlOrRd",
                legend_name="出现频次"
            ).add_to(m)

        elif geo_mode == "聚合分布点图":
            cluster = MarkerCluster().add_to(m)
            for _, row in valid_coords.iterrows():
                popup_html = f"""
                        <div style='width: 150px;'>
                            <b>识别省份:</b> {row.get('name', '未知')}<br>
                            <b>经度:</b> {row['lng']:.4f}<br>
                            <b>纬度:</b> {row['lat']:.4f}
                        </div>
                        """
                folium.CircleMarker(
                    location=[row['lat'], row['lng']],
                    radius=5, color='#FF4500', fill=True, fill_opacity=0.7,
                    popup=folium.Popup(popup_html, max_width=200)
                ).add_to(cluster)

        elif geo_mode == "无聚合散点图":
            for _, row in valid_coords.iterrows():
                folium.CircleMarker(
                    location=[row['lat'], row['lng']],
                    radius=2,
                    color='#FF4500',
                    fill=True,
                    fill_opacity=0.8,
                    weight=0
                ).add_to(m)


        # ... 前面的省级填色图、散点图、热力图代码保持不变 ...

        elif geo_mode == "空间热力图":

            heat_data = [[row['lat'], row['lng']] for index, row in valid_coords.iterrows()]

            HeatMap(heat_data, radius=15, blur=20, max_zoom=1).add_to(m)


        # 新增：MaxEnt 栅格预测图层渲染逻辑

        elif geo_mode == "MaxEnt 适生区预测":



            # 支持 .tif 或 .asc 格式

            raster_path_tif = os.path.join("data/maxent_results", f"{selected_species}.tif")
            raster_path_asc = os.path.join("data/maxent_results", f"{selected_species}.asc")
            raster_file = raster_path_tif if os.path.exists(raster_path_tif) else raster_path_asc if os.path.exists(
                raster_path_asc) else None

            if raster_file:

                with rasterio.open(raster_file) as src:
                    # 获取栅格的物理边界
                    bounds = src.bounds
                    # Folium 要求的边界格式是 [[南, 西], [北, 东]]
                    img_bounds = [[bounds.bottom, bounds.left], [bounds.top, bounds.right]]
                    # 读取第一波段数据
                    data = src.read(1)
                    nodata = src.nodata
                    # 将无数据区域（NoData）转换为 NaN，避免干扰渲染
                    if nodata is not None:
                        data = np.where(data == nodata, np.nan, data)
                    # MaxEnt 逻辑输出值域通常是 0~1，获取当前数据的实际极值用于归一化
                    vmin, vmax = np.nanmin(data), np.nanmax(data)

                    # 归一化处理矩阵，并应用 Matplotlib 的热力色带 (如 YlOrRd 或 jet)

                    norm_data = (data - vmin) / (vmax - vmin)

                    cmap = plt.get_cmap('YlOrRd')

                    rgba_img = cmap(norm_data)

                    # 处理 Alpha 透明度通道：NaN 区域完全透明 (0)，有数据的区域半透明 (0.7)

                    rgba_img[..., 3] = np.where(np.isnan(data), 0, 0.7)

                    # 将处理好的数组作为图像图层叠加到地图上

                    raster_layers.ImageOverlay(

                        image=rgba_img,

                        bounds=img_bounds,

                        opacity=0.7,

                        name='适生区预测'

                    ).add_to(m)

                    # 在地图上添加对应的图例色带

                    colormap = cm.LinearColormap(colors=['#ffffcc', '#fd8d3c', '#e31a1c'], vmin=vmin, vmax=vmax,
                                                 caption=f'{selected_species} 适生概率')

                    colormap.add_to(m)

            else:

                st.warning(f"未在 data/maxent_results 目录下找到 {selected_species} 的预测结果文件 (.tif 或 .asc)。")

        # 渲染地图

        st_folium(m, width="100%", height=600, returned_objects=[])



# --- Tab 2: 知识问答 ---
with tab2:
    # 1. 初始化欢迎语和问答状态
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant",
             "content": "你好！我是水生入侵生物综合平台的智能助手。你可以随时向我提问，例如查询物种的分类、危害、分布范围或防治手段。"}
        ]

    # 初始化快捷提问的当前物种（首次打开时随机抽取）
    if "chat_species" not in st.session_state:
        st.session_state.chat_species = random.choice(species_names) if species_names else "默认物种"

    # 2. 聊天记录展示区 (固定高度，内部滚动)
    chat_container = st.container(height=500)
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

                has_cypher = "cypher" in msg and msg["cypher"] and msg["cypher"] != "未获取到查询语句"
                has_context = "context" in msg and msg["context"]

                if has_cypher or has_context:
                    with st.expander("🔍 查看后台检索细节"):
                        if has_cypher:
                            st.markdown("**执行的 Cypher 语句：**")
                            st.code(msg["cypher"], language="cypher")
                        if has_context:
                            st.markdown("**数据库返回的原始信息 (Context)：**")
                            st.json(msg["context"])

                if "image" in msg:
                    st.image(msg["image"], width=300)

        # 3. 常驻快捷问题区 (渲染在聊天容器外部，输入框上方)
    st.markdown(f"💡 试试关于 **{st.session_state.chat_species}** 的提问：")

    current_species = st.session_state.chat_species

        # 完整的问题池
    question_pool = [
            {"label": f"介绍一下 {current_species}",
             "prompt": f"请全面介绍一下{current_species}，包括分类、危害和防治手段。"},
            {"label": f"问问 {current_species} 的危害", "prompt": f"请详细介绍一下{current_species}的危害是什么？"},
            {"label": f"如何防治 {current_species}？", "prompt": f"针对{current_species}，有哪些有效的防治手段？"},
            {"label": f"{current_species} 属于什么分类？", "prompt": f"{current_species}在生物学上属于什么分类？"},
            {"label": f"{current_species} 的原产地在哪？", "prompt": f"{current_species}的原产地是哪里？它是怎么入侵的？"}
    ]

    # --- 核心动态刷新逻辑 ---
    # 初始化状态变量
    if "last_suggested" not in st.session_state:
            st.session_state.last_suggested = []
    if "msg_count_for_sugg" not in st.session_state:
            st.session_state.msg_count_for_sugg = -1

    current_msg_count = len(st.session_state.messages)

    # 触发条件：当聊天记录增加（用户提问了），或者切换了讨论的物种时
    if current_msg_count != st.session_state.msg_count_for_sugg or st.session_state.get(
                "last_species_for_sugg") != current_species:

        # 提取上一次推荐过的问题标签
        last_labels = [q["label"] for q in st.session_state.last_suggested]

        # 从问题池中过滤掉上一次推荐过的，保证这次绝对不同
        available_pool = [q for q in question_pool if q["label"] not in last_labels]

        # 兜底：如果过滤后剩下的不够2个，就用全量池子
        if len(available_pool) < 2:
            available_pool = question_pool

        # 随机抽取2个新的
        st.session_state.last_suggested = random.sample(available_pool, 2)

        # 更新状态记录
        st.session_state.msg_count_for_sugg = current_msg_count
        st.session_state.last_species_for_sugg = current_species

    # 获取本轮应展示的随机问题
    random_questions = st.session_state.last_suggested

    # 渲染按钮
    current_prompt = None
    col_ask1, col_ask2 = st.columns(2)
    if col_ask1.button(random_questions[0]["label"], use_container_width=True):
        current_prompt = random_questions[0]["prompt"]
    if col_ask2.button(random_questions[1]["label"], use_container_width=True):
        current_prompt = random_questions[1]["prompt"]

    # 4. 底部输入框 (会自动贴在页面最底部，快捷按钮被顶在它上方)
    chat_input = st.chat_input("请输入你的问题...")
    if chat_input:
        current_prompt = chat_input

    # 5. 处理提交的问题
    if current_prompt:
        # 更新快捷提问的目标物种：检查用户输入或点击的 prompt 中是否包含已知物种
        for s in species_names:
            if s in current_prompt:
                st.session_state.chat_species = s
                break

        st.session_state.messages.append({"role": "user", "content": current_prompt})

        # 将用户问题立即显示
        with chat_container:
            with st.chat_message("user"):
                st.markdown(current_prompt)

            # 处理 AI 回答
            with st.chat_message("assistant"):
                with st.spinner("查阅知识图谱..."):
                    try:
                        chain = get_graph_chain(openai_key, neo4j_pwd)
                        response = chain.invoke({"query": current_prompt})
                        answer = response['result']

                        st.markdown(answer)

                        generated_cypher = "未获取到查询语句"
                        retrieved_context = []

                        if 'intermediate_steps' in response and len(response['intermediate_steps']) > 0:
                            generated_cypher = response['intermediate_steps'][0].get('query', "解析失败")
                            if len(response['intermediate_steps']) > 1:
                                retrieved_context = response['intermediate_steps'][1].get('context', [])
                        elif 'generated_cypher' in response:
                            generated_cypher = response['generated_cypher']

                        with st.expander("🔍 查看后台检索细节"):
                            st.markdown("**执行的 Cypher 语句：**")
                            st.code(generated_cypher, language="cypher")
                            if retrieved_context:
                                st.markdown("**数据库返回的原始信息 (Context)：**")
                                st.json(retrieved_context)

                        display_species = None
                        # 二次确认：如果回答中提到了其他物种，也同步更新界面快捷提问的目标
                        for s in species_names:
                            if s in answer or s in current_prompt:
                                display_species = s
                                st.session_state.chat_species = s
                                break

                        msg_data = {
                            "role": "assistant",
                            "content": answer,
                            "cypher": generated_cypher,
                            "context": retrieved_context
                        }

                        if display_species:
                            img_path = f"data/images/{display_species}.jpg"
                            if os.path.exists(img_path):
                                st.divider()
                                st.image(img_path, width=400, caption=f"📸 识别到的物种：{display_species}")
                                msg_data["image"] = img_path

                        st.session_state.messages.append(msg_data)
                        st.rerun()  # 强制刷新页面，使最新的快捷问题按钮生效

                    except Exception as e:
                        st.error(f"问答系统异常: {e}")

# --- Tab 3: 数据上报与更新 ---
with tab3:
    st.subheader("📝 新增物种分布记录")
    st.markdown("支持在地图上直观选点，也可使用下方表单进行文本与坐标的双向解析。确认无误后点击最下方保存。")

    if species_names:
        # 1. 初始化 Session State（加上 _widget 后缀作为专属绑定）
        if "input_addr_widget" not in st.session_state:
            st.session_state.input_addr_widget = "江苏省南京市栖霞区仙林大学城"
        if "input_lng_widget" not in st.session_state:
            st.session_state.input_lng_widget = 118.9227
        if "input_lat_widget" not in st.session_state:
            st.session_state.input_lat_widget = 32.1065
        if "geo_msg" not in st.session_state:
            st.session_state.geo_msg = None
        if "last_map_click" not in st.session_state:
            st.session_state.last_map_click = None


        # ================= 回调函数区 =================
        def forward_geocode():
            """正向解析：地名 -> 坐标"""
            addr = st.session_state.input_addr_widget
            if addr.strip():
                try:
                    geolocator = Nominatim(user_agent="aquatic_species_tracker")
                    location = geolocator.geocode(addr)
                    if location:
                        st.session_state.input_lng_widget = float(location.longitude)
                        st.session_state.input_lat_widget = float(location.latitude)
                        st.session_state.geo_msg = ("success", "正向解析成功！地图与坐标已同步。")
                    else:
                        st.session_state.geo_msg = ("error", "未能找到该地名的坐标，请尝试更换关键词。")
                except Exception as e:
                    st.session_state.geo_msg = ("error", f"解析出错: {e}")
            else:
                st.session_state.geo_msg = ("warning", "请先输入地名。")


        def reverse_geocode():
            """逆向解析：坐标 -> 地名"""
            lat = st.session_state.input_lat_widget
            lng = st.session_state.input_lng_widget
            try:
                geolocator = Nominatim(user_agent="aquatic_species_tracker")
                coord_str = f"{lat}, {lng}"
                location = geolocator.reverse(coord_str)
                if location:
                    st.session_state.input_addr_widget = location.address
                    st.session_state.geo_msg = ("success", "逆向解析成功！上方的地名已同步更新。")
                else:
                    st.session_state.geo_msg = ("error", "未能找到该坐标对应的地名。")
            except Exception as e:
                st.session_state.geo_msg = ("error", f"解析出错: {e}")


        # ===============================================

        # 显示各类提示信息
        if st.session_state.geo_msg:
            msg_type, msg_text = st.session_state.geo_msg
            if msg_type == "success":
                st.success(msg_text)
            elif msg_type == "error":
                st.error(msg_text)
            elif msg_type == "warning":
                st.warning(msg_text)
            st.session_state.geo_msg = None

            # 2. 交互式地图选点区
        st.markdown("##### 🗺️ 交互地图选点")

        # 新增底图切换控件，放置在操作指南上方
        tab3_basemap = st.radio("选择底图样式", ["街道图 (OSM)", "卫星影像 (Esri)"], horizontal=True,
                                key="tab3_basemap")
        st.info("💡 操作指南：鼠标滚轮缩放地图，左键按住拖动地图，左键单击地图任意位置可直接获取目标点坐标！")

        # 配置底图字典
        tiles_dict = {
            "街道图 (OSM)": "OpenStreetMap",
            "卫星影像 (Esri)": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        }
        attr_dict = {
            "卫星影像 (Esri)": "Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community"
        }

        # 动态创建地图，并应用用户选择的底图参数
        m_tab3 = folium.Map(
            location=[st.session_state.input_lat_widget, st.session_state.input_lng_widget],
            zoom_start=13,
            tiles=tiles_dict[tab3_basemap],
            attr=attr_dict.get(tab3_basemap, "")
        )

        # 在当前坐标位置放置一个红色的图钉
        folium.Marker(
            [st.session_state.input_lat_widget, st.session_state.input_lng_widget],
            tooltip="当前录入位置",
            icon=folium.Icon(color="red", icon="info-sign")
        ).add_to(m_tab3)

        # 渲染地图并捕获点击事件
        map_data = st_folium(m_tab3, height=400, width="100%", key="tab3_interactive_map")

        if map_data and map_data.get("last_clicked"):
            clicked_lat = map_data["last_clicked"]["lat"]
            clicked_lng = map_data["last_clicked"]["lng"]
            current_click = (clicked_lat, clicked_lng)

            if st.session_state.last_map_click != current_click:
                st.session_state.last_map_click = current_click
                st.session_state.input_lat_widget = float(clicked_lat)
                st.session_state.input_lng_widget = float(clicked_lng)

                try:

                    geolocator = Nominatim(user_agent="aquatic_species_tracker")
                    coord_str = f"{clicked_lat}, {clicked_lng}"
                    location = geolocator.reverse(coord_str)
                    if location:
                        st.session_state.input_addr_widget = location.address
                        st.session_state.geo_msg = ("success", "📍 地图选点成功！坐标与地名已自动更新。")
                    else:
                        st.session_state.input_addr_widget = "未知位置"
                        st.session_state.geo_msg = ("warning", "📍 坐标获取成功，但该位置无详细地名记录。")
                except:
                    st.session_state.input_addr_widget = "解析超时/失败"
                    st.session_state.geo_msg = ("warning", "📍 坐标获取成功。")

                st.rerun()

        # 3. 正向解析 UI
        col_addr, col_btn_fwd = st.columns([3, 1])
        with col_addr:
            st.text_input("详细地名", key="input_addr_widget", help="输入地名后点击右侧按钮可自动获取坐标")
        with col_btn_fwd:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            st.button("解析为坐标 ⬇️", use_container_width=True, on_click=forward_geocode)

        # 4. 逆向解析 UI
        col_lon, col_lat, col_btn_rev = st.columns([1.5, 1.5, 1])
        with col_lon:
            st.number_input("经度 (Longitude)", min_value=-180.0, max_value=180.0, step=0.0001, format="%.4f",
                            key="input_lng_widget")
        with col_lat:
            st.number_input("纬度 (Latitude)", min_value=-90.0, max_value=90.0, step=0.0001, format="%.4f",
                            key="input_lat_widget")
        with col_btn_rev:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            st.button("反查地名 ⬆️", use_container_width=True, on_click=reverse_geocode)

        st.divider()

        # 5. 业务数据录入与保存
        st.markdown("##### 💾 记录信息与保存")
        col_sp, col_yr = st.columns(2)
        with col_sp:
            target_species = st.selectbox("选择观测到的物种", species_names)
        with col_yr:

            new_year = st.number_input("观测年份", min_value=1900, max_value=datetime.datetime.now().year,
                                       value=datetime.datetime.now().year, step=1)

        if st.button("💾 确认保存并更新系统", type="primary", use_container_width=True):
            try:
                csv_path = os.path.join(data_dir, f"{target_species}.csv")

                if os.path.exists(csv_path):
                    df = pd.read_csv(csv_path)
                else:
                    df = pd.DataFrame(columns=['lng', 'lat', 'year'])

                new_row = pd.DataFrame([{'lng': st.session_state.input_lng_widget,
                                         'lat': st.session_state.input_lat_widget, 'year': new_year}])
                df = pd.concat([df, new_row], ignore_index=True)
                df.to_csv(csv_path, index=False)

                get_standard_province_data.clear()

                st.success(
                    f"✅ 录入成功！坐标 ({st.session_state.input_lng_widget:.4f}, {st.session_state.input_lat_widget:.4f}) 已写入 {target_species} 数据库。")
                st.info("请切换回 🌍 分布识别分析 查看新增的标点。")

            except Exception as e:
                st.error(f"保存失败: {e}")
    else:
        st.warning("暂无物种基础数据，无法进行上报操作。")