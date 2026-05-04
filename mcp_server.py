# -*- coding: utf-8 -*-
"""
天赐范式 · MCP 算子流服务（Minimal Viable API）
封装 Σ 不确定性算子、EBF 蝴蝶算子，提供 HTTP 接口
"""
from flask import Flask, request, jsonify
import numpy as np

app = Flask(__name__)

@app.route('/sigma', methods=['POST'])
def sigma_uncertainty():
    """Σ 不确定性算子"""
    data = request.json
    sigma = (np.clip(data['data_error'] / 0.5, 0, 0.35) +
             np.clip(data['model_divergence'] / 2.0, 0, 0.4) +
             np.clip(data['external_shock'] / 1.0, 0, 0.25))
    sigma = np.clip(sigma, 0.05, 0.98)
    return jsonify({"sigma": round(float(sigma), 4)})

@app.route('/ebf', methods=['POST'])
def ebf_butterfly():
    """EBF 蝴蝶算子"""
    data = request.json
    shock = data['shock']
    elasticity = data['elasticity']
    cold_response = 1.0 / (1.0 + np.exp(-15.0 * (abs(shock) - 0.3)))
    risk = cold_response * (1.0 + 5.0 * elasticity) ** 2
    risk = np.clip(risk, 0.0, 1.0)
    return jsonify({"amplified_risk": round(float(risk), 4)})

@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({"status": "ok", "framework": "天赐范式·算子流API"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)