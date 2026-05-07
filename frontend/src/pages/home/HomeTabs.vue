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
            <h4>平台核心服务能力</h4>
            <p>中国水生动物入侵智能化平台提供从数据采集到智能决策的全链条服务，覆盖科研、监测、管理全场景。</p>

            <div class="progress-container">
              <div class="title">地理可视化 100%</div>
              <div class="progress">
                <div
                  class="progress-bar first"
                  role="progressbar"
                  aria-valuenow="0"
                  aria-valuemin="0"
                  aria-valuemax="100"
                ></div>
              </div>
              <div class="title">知识图谱服务 95%</div>
              <div class="progress">
                <div
                  class="progress-bar second"
                  role="progressbar"
                  aria-valuenow="95"
                  aria-valuemin="0"
                  aria-valuemax="100"
                ></div>
              </div>
              <div class="title">数据智能分析 90%</div>
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
                <div class="media-body"><strong>前后端分离</strong> 架构，高效稳定易扩展</div>
              </li>
              <li class="media">
                <div class="media-bullet">2</div>
                <div class="media-body"><strong>多库协同</strong> 存储，结构化+关联数据统一管理</div>
              </li>
              <li class="media">
                <div class="media-bullet">3</div>
                <div class="media-body"><strong>轻量化部署</strong>，本地/公网快速上线使用</div>
              </li>
            </ul>
            <ul class="list-unstyled li-space-lg last">
              <li class="media">
                <div class="media-bullet">4</div>
                <div class="media-body"><strong>地理信息+知识图谱</strong> 深度融合创新</div>
              </li>
              <li class="media">
                <div class="media-bullet">5</div>
                <div class="media-body"><strong>智能问答</strong> 降低使用门槛，支持自然语言查询</div>
              </li>
              <li class="media">
                <div class="media-bullet">6</div>
                <div class="media-body"><strong>安全可靠</strong>，具备完善权限与数据管控机制</div>
              </li>
            </ul>
          </div>

          <div class="tab-pane fade" id="tab-3" role="tabpanel" aria-labelledby="tab-3">
            <p>
              <strong>平台全面服务</strong> 全国水生生物监测站、科研院所、生态环境管理部门，实现智能化升级。
            </p>
            <p><strong>核心价值</strong> 提升监测效率、打破数据孤岛、支撑科学决策、守护水域生态安全。</p>
            <ul class="list-unstyled li-space-lg">
              <li class="media">
                <i class="fas fa-square"></i>
                <div class="media-body">快速部署，开箱即用，降低技术使用门槛</div>
              </li>
              <li class="media">
                <i class="fas fa-square"></i>
                <div class="media-body">提供标准化数据接口，支持系统对接扩展</div>
              </li>
              <li class="media">
                <i class="fas fa-square"></i>
                <div class="media-body">持续迭代优化，适配最新监测与管理需求</div>
              </li>
              <li class="media">
                <i class="fas fa-square"></i>
                <div class="media-body">提供专属技术支持与培训服务</div>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
    <div class="area-2"></div>
  </div>
</template>
