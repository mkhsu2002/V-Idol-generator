import React, { useState } from 'react';
import { Configuration, OpenAIApi } from 'openai';
import './App.css';

const configuration = new Configuration({
  apiKey: process.env.REACT_APP_OPENAI_API_KEY
});

const openai = new OpenAIApi(configuration);

function App() {
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [inputText, setInputText] = useState(
    "一個在溫哥華長大的華裔陽光大男孩，30歲就創業成功財務自由，開始環遊世界邊寫作的人生。"
  );
  const [results, setResults] = useState({
    step1: '',
    step2: '',
    step3: '',
    step4: '',
    step5: '',
    step6: ''
  });

  const prompts = {
    step1: `你是一位專精於心理學、劇本創作的虛擬偶像人設專家。根據"${inputText}"為基礎參考來設計一個虛擬偶像的人設參數框架，須含括以下參數：基本個資、性格特徵、外觀描述、興趣愛好、背景故事等，並以表格方式列出每個類別和對應的參數名稱。`,
    step2: `你是一位專精於心理學與數據建模的虛擬偶像人設專家，致力於打造具高度實用性的人設資料。根據以下虛擬偶像的人設參數框架，請針對每個類別展開更詳細的子參數，確保參數可供後續 LLM 微調使用：\n\n${results.step1}`,
    // ... 其他步驟的提示詞
  };

  const generateStep = async () => {
    setLoading(true);
    try {
      const prompt = prompts[`step${currentStep}`];
      const response = await openai.createCompletion({
        model: "gpt-3.5-turbo",
        messages: [{ role: "user", content: prompt }],
        temperature: 0.7,
        max_tokens: 1000
      });

      setResults(prev => ({
        ...prev,
        [`step${currentStep}`]: response.data.choices[0].message.content
      }));
      
      if (currentStep < 6) {
        setCurrentStep(prev => prev + 1);
      }
    } catch (error) {
      console.error('Error:', error);
    }
    setLoading(false);
  };

  return (
    <div className="App">
      <h1>V-Idol 人設生成器</h1>
      
      <div className="input-section">
        <textarea
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="請輸入基礎描述..."
        />
      </div>

      <div className="current-step">
        <h2>當前步驟: {currentStep}/6</h2>
        <button 
          onClick={generateStep}
          disabled={loading}
        >
          {loading ? '生成中...' : '生成下一步'}
        </button>
      </div>

      <div className="results-section">
        {Object.entries(results).map(([step, result]) => (
          result && (
            <div key={step} className="result-card">
              <h3>Step {step.replace('step', '')}</h3>
              <pre>{result}</pre>
            </div>
          )
        ))}
      </div>
    </div>
  );
}

export default App; 