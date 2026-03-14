<template>
  <div class="page">
    <div class="container">
      <header class="hero">
        <div>
          <p class="eyebrow">CostPilot</p>
          <h1>AWS 비용 최적화 대시보드</h1>
          <p class="subtitle">
            EC2 사용률과 비용 데이터를 분석해 최적화 추천을 제공합니다.
          </p>
        </div>
      </header>

      <section class="panel search-panel">
        <div class="field-group">
          <label for="instanceId">EC2 Instance ID</label>
          <input
            id="instanceId"
            v-model="instanceId"
            type="text"
            placeholder="i-01b8ee61b9451d611"
          />
        </div>

        <div class="field-group">
          <label for="instanceType">Instance Type</label>
          <input
            id="instanceType"
            v-model="instanceType"
            type="text"
            placeholder="t3.large"
          />
        </div>

        <button class="analyze-btn" @click="analyze" :disabled="loading">
          {{ loading ? "분석 중..." : "분석 실행" }}
        </button>
      </section>

      <section v-if="error" class="panel error-panel">
        <h3>오류</h3>
        <p>{{ error }}</p>
      </section>

      <section v-if="result" class="dashboard">
        <div class="summary-grid">
          <div class="summary-card">
            <p class="card-label">Instance ID</p>
            <p class="card-value small">{{ result.instance_id }}</p>
          </div>

          <div class="summary-card">
            <p class="card-label">Instance Type</p>
            <p class="card-value">{{ result.instance_type }}</p>
          </div>

          <div class="summary-card">
            <p class="card-label">평균 CPU 사용률</p>
            <p class="card-value">{{ formatPercent(result.cpu_avg) }}</p>
          </div>

          <div class="summary-card">
            <p class="card-label">월 비용</p>
            <p class="card-value">{{ formatCost(result.monthly_cost) }}</p>
          </div>
        </div>

        <div class="panel recommendation-panel">
          <div class="recommendation-header">
            <div>
              <p class="section-label">추천 결과</p>
              <h2>{{ result.recommendation?.recommendation }}</h2>
            </div>
            <span class="badge" :class="badgeClass(result.recommendation?.recommendation)">
              {{ result.recommendation?.recommendation }}
            </span>
          </div>

          <div class="recommendation-grid">
            <div class="recommendation-box">
              <p class="box-label">분석 사유</p>
              <p class="box-text">{{ result.recommendation?.reason }}</p>
            </div>

            <div class="recommendation-box">
              <p class="box-label">예상 절감액</p>
              <p class="box-text strong">
                {{ formatCost(result.recommendation?.expected_saving) }}
              </p>
            </div>
          </div>
        </div>

        <details class="panel raw-panel">
          <summary>원본 응답 보기</summary>
          <pre>{{ prettyRaw }}</pre>
        </details>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from "vue";

const instanceId = ref("i-01b8ee61b9451d611");
const instanceType = ref("t3.large");
const loading = ref(false);
const error = ref("");
const result = ref(null);
const rawResponse = ref("");

// 네 실제 API Gateway URL
const API_URL =
  "https://drgr5ncy9j.execute-api.ap-northeast-2.amazonaws.com/default/analyze";

const prettyRaw = computed(() => {
  try {
    return JSON.stringify(JSON.parse(rawResponse.value), null, 2);
  } catch {
    return rawResponse.value;
  }
});

function formatPercent(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
  return `${Number(value).toFixed(2)}%`;
}

function formatCost(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
  const num = Number(value);

  if (num === 0) return "$0.00";
  if (num < 0.01) return `$${num.toFixed(6)}`;
  return `$${num.toFixed(2)}`;
}

function badgeClass(text) {
  if (!text) return "";
  if (text.includes("다운사이징")) return "warn";
  if (text.includes("업사이징")) return "info";
  return "neutral";
}

async function analyze() {
  loading.value = true;
  error.value = "";
  result.value = null;
  rawResponse.value = "";

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        instance_id: instanceId.value
      })
    });

    const text = await response.text();
    rawResponse.value = text;

    if (!response.ok) {
      throw new Error(`API 호출 실패: ${response.status} ${text}`);
    }

    const data = JSON.parse(text);
    result.value = data;
  } catch (err) {
    error.value = err.message || "오류가 발생했습니다.";
  } finally {
    loading.value = false;
  }
}
</script>

<style>
:root {
  color-scheme: light;
  font-family: Inter, Arial, sans-serif;
}

body {
  margin: 0;
  background: #f5f7fb;
}

.page {
  min-height: 100vh;
  padding: 24px 32px;
  background:
    radial-gradient(circle at top right, rgba(86, 140, 255, 0.12), transparent 30%),
    #f5f7fb;
}

.container {
  width: 100%;
  max-width: 1600px;
  margin: 0;
}

.hero {
  margin-bottom: 28px;
}

.eyebrow {
  margin: 0 0 8px;
  color: #5b6bff;
  font-weight: 700;
  font-size: 14px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.hero h1 {
  margin: 0;
  font-size: 42px;
  color: #172033;
}

.subtitle {
  margin: 10px 0 0;
  color: #5f6b7a;
  font-size: 18px;
}

.panel {
  background: #ffffff;
  border: 1px solid #e8edf5;
  border-radius: 20px;
  box-shadow: 0 10px 30px rgba(18, 38, 63, 0.06);
}

.search-panel {
  display: grid;
  grid-template-columns: 2fr 1fr 160px;
  gap: 18px;
  padding: 26px;
  align-items: end;
  margin-bottom: 28px;
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field-group label {
  font-size: 14px;
  font-weight: 600;
  color: #334155;
}

.field-group input {
  height: 50px;
  border: 1px solid #d8e0ec;
  border-radius: 12px;
  padding: 0 14px;
  font-size: 16px;
}

.analyze-btn {
  height: 50px;
  border: none;
  border-radius: 12px;
  padding: 0 20px;
  background: linear-gradient(135deg, #5b6bff, #7a5cff);
  color: white;
  font-weight: 700;
  font-size: 15px;
  cursor: pointer;
}

.dashboard {
  display: grid;
  gap: 26px;
}

.summary-grid {
  display: grid;
  grid-template-columns: 1.6fr 1fr 1fr 1.2fr;
  gap: 18px;
}

.summary-card {
  background: #fff;
  border: 1px solid #e8edf5;
  border-radius: 18px;
  padding: 26px;
  min-height: 140px;
}

.card-label {
  margin: 0 0 12px;
  color: #64748b;
  font-size: 14px;
  font-weight: 600;
}

.card-value {
  margin: 0;
  color: #172033;
  font-size: 36px;
  font-weight: 800;
}

.card-value.small {
  font-size: 26px;
  word-break: break-all;
}

.recommendation-panel {
  padding: 30px;
}

.section-label {
  margin: 0 0 8px;
  color: #64748b;
  font-size: 13px;
  font-weight: 700;
}

.recommendation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.recommendation-header h2 {
  margin: 0;
  font-size: 34px;
}

.badge {
  border-radius: 999px;
  padding: 10px 16px;
  font-size: 13px;
  font-weight: 700;
}

.badge.warn {
  background: #fff4e5;
  color: #b76a00;
}

.badge.info {
  background: #eaf3ff;
  color: #0b63ce;
}

.badge.neutral {
  background: #eef2f7;
  color: #475569;
}

.recommendation-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 18px;
}

.recommendation-box {
  border: 1px solid #e8edf5;
  border-radius: 16px;
  padding: 22px;
  background: #fafcff;
}

.box-label {
  margin: 0 0 10px;
  color: #64748b;
  font-size: 13px;
  font-weight: 700;
}

.box-text {
  margin: 0;
  font-size: 17px;
}

.box-text.strong {
  font-size: 32px;
  font-weight: 800;
}

.raw-panel {
  padding: 20px 24px;
}

.raw-panel summary {
  cursor: pointer;
  font-weight: 700;
  color: #334155;
}

.raw-panel pre {
  margin-top: 16px;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 13px;
  color: #334155;
  background: #f8fafc;
  border-radius: 12px;
  padding: 14px;
  border: 1px solid #e8edf5;
}

.error-panel {
  padding: 18px 20px;
  border-color: #ffd7d7;
  background: #fff7f7;
  color: #b42318;
}

.error-panel h3 {
  margin-top: 0;
}

@media (max-width: 1024px) {
  .search-panel,
  .summary-grid,
  .recommendation-grid {
    grid-template-columns: 1fr;
  }

  .hero h1 {
    font-size: 32px;
  }
}
</style>