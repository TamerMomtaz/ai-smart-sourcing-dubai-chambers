import React from 'react';

const AIInteractionCard = ({ interaction }) => {
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const getModelColor = (modelName) => {
    if (modelName?.includes('claude')) return 'bg-teal/10 text-teal';
    if (modelName?.includes('gpt') || modelName?.includes('openai')) return 'bg-gold/10 text-gold';
    if (modelName?.includes('gemini')) return 'bg-burgundy/10 text-burgundy';
    return 'bg-ink/10 text-ink';
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-4 border border-ink/10">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-2">
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-body font-medium ${getModelColor(interaction.model_name)}`}>
              {interaction.model_name}
            </span>
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-body font-medium bg-ink/10 text-ink">
              {interaction.operation_type}
            </span>
          </div>
          <p className="text-xs font-body text-ink/60">{formatDate(interaction.timestamp)}</p>
        </div>
        <div className="text-right">
          <p className="text-lg font-heading font-bold text-teal">
            ${interaction.cost_usd?.toFixed(4) || '0.0000'}
          </p>
          <p className="text-xs font-body text-ink/60">{interaction.latency_ms}ms</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3 text-sm font-body">
        <div>
          <span className="text-ink/60">Prompt:</span>
          <p className="text-ink font-medium">{interaction.prompt_tokens} tokens</p>
        </div>
        <div>
          <span className="text-ink/60">Completion:</span>
          <p className="text-ink font-medium">{interaction.completion_tokens} tokens</p>
        </div>
        <div>
          <span className="text-ink/60">ΣI Units:</span>
          <p className="text-ink font-medium">{interaction.intelligence_units?.toFixed(2) || '0.00'}</p>
        </div>
      </div>

      {(interaction.energy_kwh || interaction.carbon_gco2) && (
        <div className="mt-3 pt-3 border-t border-ink/10 flex items-center space-x-4 text-xs font-body text-ink/60">
          {interaction.energy_kwh && (
            <div>
              <span>Energy:</span>
              <span className="ml-1 font-medium">{interaction.energy_kwh.toFixed(6)} kWh</span>
            </div>
          )}
          {interaction.carbon_gco2 && (
            <div>
              <span>Carbon:</span>
              <span className="ml-1 font-medium">{interaction.carbon_gco2.toFixed(4)} gCO₂</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AIInteractionCard;