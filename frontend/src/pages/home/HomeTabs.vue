<script setup>
import { onMounted } from 'vue'

onMounted(() => {
  // Bootstrap tabs will be initialized by scripts.js
  // The tab markup uses data-toggle="tab" which Bootstrap handles
})
</script>

<template>
  <div class="tabs">
    <div class="area-1">
      <div class="tabs-container">
        <ul class="nav nav-tabs" id="ariaTabs" role="tablist">
          <li class="nav-item">
            <a
              class="nav-link active"
              id="nav-tab-1"
              data-toggle="tab"
              href="#tab-1"
              role="tab"
              aria-controls="tab-1"
              aria-selected="true"
            >
              <i class="fas fa-th"></i> 平台能力
            </a>
          </li>
          <li class="nav-item">
            <a
              class="nav-link"
              id="nav-tab-2"
              data-toggle="tab"
              href="#tab-2"
              role="tab"
              aria-controls="tab-2"
              aria-selected="false"
            >
              <i class="fas fa-th"></i> 技术优势
            </a>
          </li>
          <li class="nav-item">
            <a
              class="nav-link"
              id="nav-tab-3"
              data-toggle="tab"
              href="#tab-3"
              role="tab"
              aria-controls="tab-3"
              aria-selected="false"
            >
              <i class="fas fa-th"></i> 应用价值
            </a>
          </li>
        </ul>

        <div class="tab-content" id="ariaTabsContent">
          <div class="tab-pane fade show active" id="tab-1" role="tabpanel" aria-labelledby="tab-1">
            <h4>核心服务：全链路生态辅助决策</h4>
            <p>AquaSIG平台打通了从非结构化文献到结构化空间知识的全链路，覆盖生态监测、科研分析与渔政管理全场景。</p>

            <div class="progress-container">
              <div class="title">WebGIS 时空动态演变感知 90%</div>
              <div class="progress">
                <div
                  class="progress-bar third"
                  role="progressbar"
                  aria-valuenow="90"
                  aria-valuemin="0"
                  aria-valuemax="100"
                ></div>
              </div>
              <div class="title">GraphRAG 零幻觉智能问答 90%</div>
              <div class="progress">
                <div
                  class="progress-bar third"
                  role="progressbar"
                  aria-valuenow="90"
                  aria-valuemin="0"
                  aria-valuemax="100"
                ></div>
              </div>
              <div class="title">多源异构数据自动化抽取 90%</div>
              <div class="progress">
                <div
                  class="progress-bar third"
                  role="progressbar"
                  aria-valuenow="90"
                  aria-valuemin="0"
                  aria-valuemax="100"
                ></div>
              </div>
            </div>
          </div>

          <div class="tab-pane fade" id="tab-2" role="tabpanel" aria-labelledby="tab-2">
            <ul class="list-unstyled li-space-lg first">
              <li class="media">
                <div class="media-bullet">1</div>
                <div class="media-body"><strong>LLM 零样本抽取：</strong>依托大模型推理能力，实现非结构化生态文本的自动化建库。</div>
              </li>
              <li class="media">
                <div class="media-bullet">2</div>
                <div class="media-body"><strong>图-表混合双引擎：</strong>Neo4j + SQLite 协同持久化，实现图谱与关系数据的极速检索。</div>
              </li>
              <li class="media">
                <div class="media-bullet">3</div>
                <div class="media-body"><strong>现代化异步架构：</strong>基于 Vue 3 + FastAPI，保障空间数据与流式问答的高效响应。</div>
              </li>
            </ul>
            <ul class="list-unstyled li-space-lg last">
              <li class="media">
                <div class="media-bullet">4</div>
                <div class="media-body"><strong>GraphRAG 增强生成：</strong>注入图谱确切事实，显著缓解大模型在垂直领域的“知识幻觉”。</div>
              </li>
              <li class="media">
                <div class="media-bullet">5</div>
                <div class="media-body"><strong>海量空间坐标聚合：</strong>集成前端空间索引，突破 Web 端高密度散点的地图渲染瓶颈。</div>
              </li>
              <li class="media">
                <div class="media-bullet">6</div>
                <div class="media-body"><strong>四元组本体设计：</strong>定制四元组生态本体，精准表达入侵物种的复杂时空演变网络。</div>
              </li>
            </ul>
          </div>

          <div class="tab-pane fade" id="tab-3" role="tabpanel" aria-labelledby="tab-3">
            <p>
              <strong>多维赋能：</strong> 平台全面服务于各级渔政管理部门、科研院所及社会公众，实现水生生物监测体系的数智化升级。
            </p>
            <p><strong>核心价值：</strong> 提升宏观监测效率、打破生态数据孤岛、支撑科学防灾决策、守护国家水域生物安全。</p>
            <ul class="list-unstyled li-space-lg">
              <li class="media">
                <i class="fas fa-square"></i>
                <div class="media-body"><strong>宏观决策支持：</strong>为渔政部门提供多级行政区划的灾情研判、热力聚集分析与扩散风险预警。</div>
              </li>
              <li class="media">
                <i class="fas fa-square"></i>
                <div class="media-body"><strong>科研分析辅助：</strong>支撑生态学家的空间缓冲区评估、时空演变分析与生物多样性溯源。</div>
              </li>
              <li class="media">
                <i class="fas fa-square"></i>
                <div class="media-body"><strong>公众生态科普：</strong>以“所查即所得”的自然语言问答交互，大幅降低专业防灾知识的获取门槛。</div>
              </li>
              <li class="media">
                <i class="fas fa-square"></i>
                <div class="media-body"><strong>众包数据闭环：</strong>建立“公众发现-坐标上报-审核入库-图谱更新”的动态持续生态监测体系。</div>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
    <div class="area-2"></div>
  </div>
</template>
