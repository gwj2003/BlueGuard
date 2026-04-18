<script setup>
const props = defineProps({
  variant: {
    type: String,
    default: 'home',
  },
})
</script>

<template>
  <div class="footer">
    <div class="container">
      <div class="row" v-if="variant === 'home'">
        <div class="col-md-6">
          <div class="text-container about">
            <h4>中国水生动物入侵智能化平台</h4>
            <p class="white">
              面向全国水域生态安全，提供水生入侵动物智能化监测、数据分析、知识服务与决策支撑，守护生物多样性与生态平衡。
            </p>
          </div>
        </div>
        <div class="col-md-2">
          <div class="text-container">
            <h4>平台链接</h4>
            <ul class="list-unstyled li-space-lg white">
              <li><a class="white" href="#your-link">平台首页</a></li>
              <li><a class="white" href="terms-conditions.html">服务条款</a></li>
              <li><a class="white" href="privacy-policy.html">隐私说明</a></li>
            </ul>
          </div>
        </div>
        <div class="col-md-2">
          <div class="text-container">
            <h4>技术支持</h4>
            <ul class="list-unstyled li-space-lg">
              <li><a class="white" href="#your-link">使用文档</a></li>
              <li><a class="white" href="#your-link">常见问题</a></li>
              <li class="media"><a class="white" href="#your-link">服务热线</a></li>
            </ul>
          </div>
        </div>
        <div class="col-md-2">
          <div class="text-container">
            <h4>合作单位</h4>
            <ul class="list-unstyled li-space-lg">
              <li><a class="white" href="#your-link">监测机构</a></li>
              <li><a class="white" href="#your-link">科研院所</a></li>
              <li><a class="white" href="#your-link">管理部门</a></li>
            </ul>
          </div>
        </div>
      </div>

      <div class="row" v-else>
        <div class="col-md-6">
          <div class="text-container about">
            <h4>Few Words About Aria</h4>
            <p class="white">
              We're passionate about creating the best mobile apps for personal develop passionate about creating the best mobile apps for. Personal develop passionate about creating the best mobile apps.
            </p>
          </div>
        </div>
        <div class="col-md-2">
          <div class="text-container">
            <h4>Links</h4>
            <ul class="list-unstyled li-space-lg white">
              <li><a class="white" href="#your-link">startupguide.com</a></li>
              <li><a class="white" href="terms-conditions.html">Terms & Conditions</a></li>
              <li><a class="white" href="privacy-policy.html">Privacy Policy</a></li>
            </ul>
          </div>
        </div>
        <div class="col-md-2">
          <div class="text-container">
            <h4>Tools</h4>
            <ul class="list-unstyled li-space-lg">
              <li><a class="white" href="#your-link">startupguide.com</a></li>
              <li><a class="white" href="terms-conditions.html">Terms & Conditions</a></li>
              <li class="media"><a class="white" href="privacy-policy.html">Privacy Policy</a></li>
            </ul>
          </div>
        </div>
        <div class="col-md-2">
          <div class="text-container">
            <h4>Partners</h4>
            <ul class="list-unstyled li-space-lg">
              <li><a class="white" href="#your-link">startupguide.com</a></li>
              <li><a class="white" href="terms-conditions.html">Terms & Conditions</a></li>
              <li><a class="white" href="privacy-policy.html">Privacy Policy</a></li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="copyright" v-if="variant === 'home'">
    <div class="container">
      <div class="row">
        <div class="col-lg-12">
          <p class="p-small">版权所有 &copy; 2025 中国水生动物入侵智能化监测与分析平台 保留所有权利。</p>
        </div>
      </div>
    </div>
  </div>

  <div class="copyright" v-else>
    <div class="container">
      <div class="row">
        <div class="col-lg-12">
          <p class="p-small">
            Copyright &copy; 2020.Company name All rights reserved.
            <a target="_blank" href="http://sc.chinaz.com/moban/">网页模板</a>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
