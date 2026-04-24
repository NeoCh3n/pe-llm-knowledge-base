import React, { useState, useEffect } from 'react';
import { Settings, Save, RotateCcw, Server, Key, Link2, Bot } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Alert, AlertDescription } from './ui/alert';
import { getLLMConfig, updateLLMConfig, type LLMConfig } from '../lib/api';

const DEFAULT_CONFIG: LLMConfig = {
  llm_provider: 'openai_compatible',
  llm_model: 'Qwen/Qwen2.5-7B-Instruct',
  llm_base_url: 'http://localhost:8001/v1',
  llm_api_key: null,
};

const PRESET_CONFIGS = {
  lmstudio: {
    name: 'LM Studio',
    llm_provider: 'openai_compatible',
    llm_model: 'local-model',
    llm_base_url: 'http://localhost:1234/v1',
  },
  ollama: {
    name: 'Ollama',
    llm_provider: 'openai_compatible',
    llm_model: 'llama2',
    llm_base_url: 'http://localhost:11434/v1',
  },
  vllm: {
    name: 'vLLM',
    llm_provider: 'openai_compatible',
    llm_model: 'Qwen/Qwen2.5-7B-Instruct',
    llm_base_url: 'http://localhost:8000/v1',
  },
};

export function SettingsPage() {
  const [config, setConfig] = useState<LLMConfig>(DEFAULT_CONFIG);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    setIsLoading(true);
    try {
      const data = await getLLMConfig();
      setConfig(data);
    } catch (error) {
      setMessage({
        type: 'error',
        text: error instanceof Error ? error.message : 'Failed to load configuration',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    setMessage(null);
    try {
      await updateLLMConfig(config);
      setMessage({ type: 'success', text: 'Configuration saved successfully!' });
    } catch (error) {
      setMessage({
        type: 'error',
        text: error instanceof Error ? error.message : 'Failed to save configuration',
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    setConfig(DEFAULT_CONFIG);
    setMessage(null);
  };

  const applyPreset = (preset: keyof typeof PRESET_CONFIGS) => {
    const presetConfig = PRESET_CONFIGS[preset];
    setConfig((prev) => ({
      ...prev,
      ...presetConfig,
    }));
    setMessage(null);
  };

  return (
    <div className="h-full overflow-auto p-6">
      <div className="mx-auto max-w-3xl">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-500">Configure your local LLM connection</p>
        </div>

        {message && (
          <Alert
            className={`mb-6 ${message.type === 'success' ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}`}
          >
            <AlertDescription
              className={message.type === 'success' ? 'text-green-700' : 'text-red-700'}
            >
              {message.text}
            </AlertDescription>
          </Alert>
        )}

        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bot size={20} />
              Quick Presets
            </CardTitle>
            <CardDescription>Select a preset configuration for common local LLM setups</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-3">
              {Object.entries(PRESET_CONFIGS).map(([key, preset]) => (
                <Button
                  key={key}
                  variant="outline"
                  onClick={() => applyPreset(key as keyof typeof PRESET_CONFIGS)}
                  className="flex items-center gap-2"
                >
                  <Server size={16} />
                  {preset.name}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings size={20} />
              LLM Configuration
            </CardTitle>
            <CardDescription>Configure connection to your local or remote LLM service</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="provider" className="flex items-center gap-2">
                <Bot size={16} />
                Provider
              </Label>
              <Input
                id="provider"
                value={config.llm_provider}
                onChange={(e) => setConfig((prev) => ({ ...prev, llm_provider: e.target.value }))}
                placeholder="openai_compatible"
                disabled={isLoading}
              />
              <p className="text-xs text-gray-500">
                Use &quot;openai_compatible&quot; for LM Studio, Ollama, vLLM, etc.
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="model" className="flex items-center gap-2">
                <Server size={16} />
                Model Name
              </Label>
              <Input
                id="model"
                value={config.llm_model}
                onChange={(e) => setConfig((prev) => ({ ...prev, llm_model: e.target.value }))}
                placeholder="Qwen/Qwen2.5-7B-Instruct"
                disabled={isLoading}
              />
              <p className="text-xs text-gray-500">
                The model identifier used by your LLM service
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="baseUrl" className="flex items-center gap-2">
                <Link2 size={16} />
                Base URL
              </Label>
              <Input
                id="baseUrl"
                value={config.llm_base_url}
                onChange={(e) => setConfig((prev) => ({ ...prev, llm_base_url: e.target.value }))}
                placeholder="http://localhost:8001/v1"
                disabled={isLoading}
              />
              <p className="text-xs text-gray-500">
                The API endpoint URL (e.g., http://localhost:1234/v1 for LM Studio)
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="apiKey" className="flex items-center gap-2">
                <Key size={16} />
                API Key (Optional)
              </Label>
              <Input
                id="apiKey"
                type="password"
                value={config.llm_api_key || ''}
                onChange={(e) =>
                  setConfig((prev) => ({
                    ...prev,
                    llm_api_key: e.target.value || null,
                  }))
                }
                placeholder="sk-..."
                disabled={isLoading}
              />
              <p className="text-xs text-gray-500">
                Optional. Most local LLMs don&apos;t require an API key, but OpenAI-compatible clients need a non-empty value.
              </p>
            </div>

            <div className="flex gap-3 pt-4">
              <Button onClick={handleSave} disabled={isLoading || isSaving} className="flex items-center gap-2">
                <Save size={16} />
                {isSaving ? 'Saving...' : 'Save Configuration'}
              </Button>
              <Button
                variant="outline"
                onClick={handleReset}
                disabled={isLoading || isSaving}
                className="flex items-center gap-2"
              >
                <RotateCcw size={16} />
                Reset to Default
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Common Local LLM Setups</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm text-gray-600">
            <div>
              <p className="font-medium text-gray-900">LM Studio</p>
              <p>1. Load a model in LM Studio</p>
              <p>2. Start the Local Server (default port 1234)</p>
              <p>3. Set Base URL to: http://localhost:1234/v1</p>
            </div>
            <div>
              <p className="font-medium text-gray-900">Ollama</p>
              <p>1. Run: ollama serve</p>
              <p>2. Set Base URL to: http://localhost:11434/v1</p>
            </div>
            <div>
              <p className="font-medium text-gray-900">vLLM</p>
              <p>1. Start vLLM server with --api-key flag if needed</p>
              <p>2. Set Base URL to: http://localhost:8000/v1</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
