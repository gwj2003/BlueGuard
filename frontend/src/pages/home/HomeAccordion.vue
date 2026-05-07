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
              ><span class="accordion-title">平台如何解决行业痛点</span>
            </span>
          </div>
          <div id="collapseOne" class="collapse show" aria-labelledby="headingOne" data-parent="#accordionOne">
            <div class="accordion-body">
              平台解决传统监测数据分散、可视化弱、知识孤立等问题，实现监测—分析—决策全流程智能化，大幅提升工作效率。
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
              <span class="circle-numbering">2</span><span class="accordion-title">前后端分离先进架构</span>
            </span>
          </div>
          <div id="collapseTwo" class="collapse" aria-labelledby="headingTwo" data-parent="#accordionOne">
            <div class="accordion-body">
              采用 Vue3 + FastAPI 前后端分离架构，模块化、低耦合、易扩展，支持高并发地理数据处理与快速部署。
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
              <span class="circle-numbering">3</span><span class="accordion-title">多技术融合创新应用</span>
            </span>
          </div>
          <div id="collapseThree" class="collapse" aria-labelledby="headingThree" data-parent="#accordionOne">
            <div class="accordion-body">
              融合地理信息、知识图谱、数据管理、智能问答，为水生入侵动物防控提供一站式技术支撑。
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
