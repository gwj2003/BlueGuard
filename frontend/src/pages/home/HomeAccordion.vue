<script setup>
import { onMounted } from 'vue'

onMounted(() => {
  // Bootstrap collapse will be initialized by scripts.js
  // The accordion markup uses data-toggle="collapse" which Bootstrap handles
})
</script>

<template>
  <div id="details" class="accordion">
    <div class="area-1"></div>
    <div class="area-2">
      <div class="accordion-container" id="accordionOne">
        <h2>科技赋能水域生态安全，智能守护生物多样性</h2>

        <div class="item">
          <div id="headingOne">
            <span
              data-toggle="collapse"
              data-target="#collapseOne"
              aria-expanded="true"
              aria-controls="collapseOne"
              role="button"
            >
              <span class="circle-numbering">1</span
              ><span class="accordion-title">打破数据孤岛与事实幻觉</span>
            </span>
          </div>
          <div id="collapseOne" class="collapse show" aria-labelledby="headingOne" data-parent="#accordionOne">
            <div class="accordion-body">
              针对传统生态数据异构分散、静态制图维度单一以及通用大模型易产生“知识幻觉”等核心痛点，平台打通了从众包采集、态势感知到防灾智答的全流程闭环，全面赋能科学治理。
            </div>
          </div>
        </div>

        <div class="item">
          <div id="headingTwo">
            <span
              class="collapsed"
              data-toggle="collapse"
              data-target="#collapseTwo"
              aria-expanded="false"
              aria-controls="collapseTwo"
              role="button"
            >
              <span class="circle-numbering">2</span><span class="accordion-title">图-表混合双引擎与高并发服务</span>
            </span>
          </div>
          <div id="collapseTwo" class="collapse" aria-labelledby="headingTwo" data-parent="#accordionOne">
            <div class="accordion-body">
              基于 Vue3 + FastAPI 现代化异步架构，底层创新融合“Neo4j图谱 + SQLite关系型”混合存储。既支持海量时空坐标的高帧率聚合渲染，又保障了复杂生态网络多跳检索的极速响应。
            </div>
          </div>
        </div>

        <div class="item">
          <div id="headingThree">
            <span
              class="collapsed"
              data-toggle="collapse"
              data-target="#collapseThree"
              aria-expanded="false"
              aria-controls="collapseThree"
              role="button"
            >
              <span class="circle-numbering">3</span><span class="accordion-title">WebGIS + GraphRAG 双核驱动</span>
            </span>
          </div>
          <div id="collapseThree" class="collapse" aria-labelledby="headingThree" data-parent="#accordionOne">
            <div class="accordion-body">
              跨界融合 WebGIS 空间拓扑分析与图检索增强生成（GraphRAG）前沿技术。以时空知识图谱为底座，实现灾情演变的动态可视化与“零幻觉、全溯源”的智能化防灾决策支撑。
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
