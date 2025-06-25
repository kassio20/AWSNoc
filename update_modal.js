function displayAlertModal(alert) {
    const modal = document.getElementById('alertModal');
    const detailsContainer = document.getElementById('alert-details');

    let aiAnalysisHtml = '';
    if (alert.ai_analysis) {
        const analysis = typeof alert.ai_analysis === 'string' ? JSON.parse(alert.ai_analysis) : alert.ai_analysis;
        aiAnalysisHtml = `
            <div class="ai-analysis">
                <h4>🤖 Análise de IA (Atual)</h4>
                <pre style="white-space: pre-wrap; font-family: monospace; font-size: 0.9rem;">${JSON.stringify(analysis, null, 2)}</pre>
            </div>
        `;
    }

    detailsContainer.innerHTML = `
        <h2 style="color: #f85149; margin-bottom: 1rem;">${alert.title}</h2>
        
        <div style="margin-bottom: 1rem;">
            <strong>Descrição:</strong><br>
            ${alert.description || 'Sem descrição disponível'}
        </div>

        <div style="margin-bottom: 1rem;">
            <strong>Detalhes do Recurso:</strong><br>
            <code style="background: rgba(45, 51, 59, 0.5); padding: 0.5rem; border-radius: 4px; display: block; margin-top: 0.5rem;">
                ID: ${alert.resource_id}<br>
                Tipo: ${alert.resource_type}<br>
                Severidade: ${alert.severity}<br>
                Status: ${alert.status}
            </code>
        </div>

        <div style="margin-bottom: 1rem;">
            <strong>Temporização:</strong><br>
            Detectado em: ${new Date(alert.created_at).toLocaleString('pt-BR')}<br>
            ${alert.resolved_at ? `Resolvido em: ${new Date(alert.resolved_at).toLocaleString('pt-BR')}` : 'Ainda não resolvido'}
        </div>

        <div style="margin-bottom: 1rem;">
            <button id="analyze-btn-${alert.id}" onclick="analyzeAlertWithAI(${alert.id})" 
                    style="background: #238636; color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 6px; cursor: pointer; font-size: 1rem;">
                🧠 Executar Análise Inteligente de IA
            </button>
        </div>

        <div id="ai-analysis-result" style="margin-top: 1rem;"></div>

        ${aiAnalysisHtml}
    `;

    modal.style.display = 'block';
}

async function analyzeAlertWithAI(alertId) {
    try {
        const button = document.getElementById(`analyze-btn-${alertId}`);
        button.disabled = true;
        button.textContent = '🔄 Executando análise detalhada...';
        button.style.background = '#6c757d';

        document.getElementById('ai-analysis-result').innerHTML = `
            <div style="text-align: center; padding: 1rem; background: rgba(88, 166, 255, 0.1); border-radius: 8px;">
                <div class="spinner"></div>
                <p>🧠 IA analisando logs, configurações e executando diagnóstico completo...</p>
                <p><small>Isso pode levar alguns minutos</small></p>
            </div>
        `;

        const response = await fetch(`${API_BASE}/api/v1/alerts/${alertId}/analyze`, {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok) {
            const analysis = data.analysis;
            
            // Formatar resultado da análise
            let resultHtml = `
                <div style="background: rgba(88, 166, 255, 0.1); border-left: 4px solid #58a6ff; padding: 1rem; border-radius: 8px;">
                    <h4 style="color: #58a6ff; margin-bottom: 1rem;">🧠 Resultado da Análise Inteligente</h4>
            `;

            if (analysis.ai_analysis && !analysis.ai_analysis.startsWith('Erro')) {
                resultHtml += `
                    <div style="background: #0d1117; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                        <h5 style="color: #7dd3fc; margin-bottom: 0.5rem;">💡 Diagnóstico da IA:</h5>
                        <div style="white-space: pre-wrap; font-family: 'Segoe UI', sans-serif; line-height: 1.5; color: #e6edf3;">
                            ${analysis.ai_analysis}
                        </div>
                    </div>
                `;
            }

            if (analysis.task_failures && analysis.task_failures.length > 0) {
                resultHtml += `
                    <div style="margin-bottom: 1rem;">
                        <h5 style="color: #f85149; margin-bottom: 0.5rem;">❌ Falhas de Tasks Detectadas:</h5>
                        ${analysis.task_failures.map(failure => `
                            <div style="background: rgba(248, 81, 73, 0.1); padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem;">
                                <strong>Motivo:</strong> ${failure.stopped_reason}<br>
                                <strong>Hora:</strong> ${failure.stopped_at}<br>
                                ${failure.containers.map(c => `<strong>Container ${c.name}:</strong> Exit code ${c.exit_code}`).join('<br>')}
                            </div>
                        `).join('')}
                    </div>
                `;
            }

            if (analysis.container_logs && analysis.container_logs.length > 0) {
                resultHtml += `
                    <div style="margin-bottom: 1rem;">
                        <h5 style="color: #79c0ff; margin-bottom: 0.5rem;">📋 Logs Analisados:</h5>
                        ${analysis.container_logs.map(log => `
                            <div style="background: rgba(121, 192, 255, 0.1); padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem;">
                                <strong>Container:</strong> ${log.container}<br>
                                <strong>Log Group:</strong> ${log.log_group}<br>
                                ${log.error ? `<span style="color: #f85149;">Erro: ${log.error}</span>` : 'Logs analisados com sucesso'}
                            </div>
                        `).join('')}
                    </div>
                `;
            }

            resultHtml += `
                    <div style="font-size: 0.8rem; color: #7d8590; margin-top: 1rem;">
                        <strong>Status:</strong> ${analysis.status}<br>
                        <strong>Timestamp:</strong> ${new Date(analysis.timestamp).toLocaleString('pt-BR')}<br>
                        <strong>Tipo de Análise:</strong> ${analysis.type}
                    </div>
                </div>
            `;

            document.getElementById('ai-analysis-result').innerHTML = resultHtml;
        } else {
            throw new Error(data.detail || 'Erro desconhecido');
        }

        button.disabled = false;
        button.textContent = '✅ Análise Concluída';
        button.style.background = '#28a745';

    } catch (error) {
        console.error('Erro na análise de IA:', error);
        document.getElementById('ai-analysis-result').innerHTML = `
            <div style="background: rgba(248, 81, 73, 0.1); border-left: 4px solid #f85149; padding: 1rem; border-radius: 8px; color: #f85149;">
                <h4>❌ Erro na Análise</h4>
                <p>${error.message}</p>
            </div>
        `;

        const button = document.getElementById(`analyze-btn-${alertId}`);
        button.disabled = false;
        button.textContent = '🧠 Tentar Análise Novamente';
        button.style.background = '#dc3545';
    }
}
