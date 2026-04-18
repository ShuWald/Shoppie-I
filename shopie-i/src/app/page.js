"use client";

import { useState, useEffect } from "react";

export default function Home() {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchTrendingProducts();
  }, []);

  const fetchTrendingProducts = async () => {
    try {
      setLoading(true);
      const response = await fetch("http://localhost:8000/api/evaluate-trending-products");
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setReport(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-yellow-600";
    return "text-red-600";
  };

  const getScoreBgColor = (score) => {
    if (score >= 80) return "bg-green-100";
    if (score >= 60) return "bg-yellow-100";
    return "bg-red-100";
  };

  const getRiskColor = (risk) => {
    switch (risk) {
      case "low": return "text-green-600";
      case "medium": return "text-yellow-600";
      case "high": return "text-red-600";
      default: return "text-gray-600";
    }
  };

  const getActionColor = (action) => {
    return action === "Distribute existing product" 
      ? "text-blue-600 bg-blue-100" 
      : "text-purple-600 bg-purple-100";
  };

  const parseInsightCard = (insight) => {
    // Parse insight strings into structured card data
    if (insight.includes("Most trending category")) {
      const match = insight.match(/Most trending category: (.+) \((\d+) products\)/);
      return {
        title: "Top Category",
        value: match ? match[1] : "N/A",
        subtitle: match ? `${match[2]} products` : "No data",
        valueClass: "text-base font-bold" // Smaller font for category names
      };
    }
    if (insight.includes("Average PoP relevance score")) {
      const match = insight.match(/Average PoP relevance score: ([\d.]+)/);
      return {
        title: "Avg PoP Score",
        value: match ? parseFloat(match[1]).toFixed(1) : "N/A",
        subtitle: "across all products",
        valueClass: "text-2xl font-bold" // Match READY FOR DISTRIBUTION tile spacing
      };
    }
    if (insight.includes("Products ready for distribution")) {
      const match = insight.match(/Products ready for distribution: (\d+)/);
      return {
        title: "Ready for Distribution",
        value: match ? match[1] : "0",
        subtitle: "products"
      };
    }
    if (insight.includes("Products requiring development")) {
      const match = insight.match(/Products requiring development: (\d+)/);
      return {
        title: "Needs Development",
        value: match ? match[1] : "0",
        subtitle: "products"
      };
    }
    if (insight.includes("High-risk products")) {
      const match = insight.match(/High-risk products requiring careful review: (\d+)/);
      return {
        title: "High-Risk Review",
        value: match ? match[1] : "0",
        subtitle: match && match[1] === "1" ? "product flagged" : "products flagged"
      };
    }
    if (insight.includes("Top opportunity")) {
      const match = insight.match(/Top opportunity: (.+) \(Score: ([\d.]+)\)/);
      return {
        title: "Top Opportunity",
        value: match ? match[1] : "N/A",
        subtitle: match ? `PoP score ${match[2]}` : "No score",
        valueClass: "text-base font-bold" // Smaller font for long product names
      };
    }
    // Default fallback
    return {
      title: "Insight",
      value: insight,
      subtitle: ""
    };
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Analyzing trending health & wellness products...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">Error: {error}</p>
          <button 
            onClick={fetchTrendingProducts}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              {/* Prince of Peace Logo */}
              <img 
                src="/PoPLogo.webp" 
                alt="Prince of Peace Logo" 
                className="h-12 w-auto object-contain"
              />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  Product Trend Dashboard
                </h1>
                <p className="text-sm text-gray-600 mt-1">
                  Smart shopping assistant for business buyers
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <button 
                onClick={fetchTrendingProducts}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
              >
                Refresh Analysis
              </button>
              {/* User Profile Icon */}
              <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center hover:bg-gray-300 transition-colors cursor-pointer">
                <svg className="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Summary Insights */}
        <div className="mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Key Insights</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            {report.summary_insights.map((insight, index) => {
              const cardData = parseInsightCard(insight);
              return (
                <div key={index} className="bg-white rounded-lg shadow p-4 border border-gray-200 hover:shadow-md transition-shadow">
                  <p className="text-sm text-gray-500 uppercase tracking-wide">{cardData.title}</p>
                  <p className={`${cardData.valueClass || "text-2xl font-bold"} text-gray-900 mt-1`}>{cardData.value}</p>
                  <p className="text-sm text-gray-600 mt-1">{cardData.subtitle}</p>
                </div>
              );
            })}
          </div>
        </div>

        {/* High Priority Products */}
        {report.high_priority_products.length > 0 && (
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              High Priority Opportunities ({report.high_priority_products.length})
            </h2>
            <div className="space-y-4">
              {report.high_priority_products.map((evaluation, index) => (
                <ProductCard 
                  key={index} 
                  evaluation={evaluation} 
                  getScoreColor={getScoreColor}
                  getScoreBgColor={getScoreBgColor}
                  getRiskColor={getRiskColor}
                  getActionColor={getActionColor}
                />
              ))}
            </div>
          </div>
        )}

        {/* Medium Priority Products */}
        {report.medium_priority_products.length > 0 && (
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Medium Priority Considerations ({report.medium_priority_products.length})
            </h2>
            <div className="space-y-4">
              {report.medium_priority_products.map((evaluation, index) => (
                <ProductCard 
                  key={index} 
                  evaluation={evaluation} 
                  getScoreColor={getScoreColor}
                  getScoreBgColor={getScoreBgColor}
                  getRiskColor={getRiskColor}
                  getActionColor={getActionColor}
                />
              ))}
            </div>
          </div>
        )}

        {/* Low Priority Products */}
        {report.low_priority_products.length > 0 && (
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Low Priority ({report.low_priority_products.length})
            </h2>
            <div className="space-y-4">
              {report.low_priority_products.map((evaluation, index) => (
                <ProductCard 
                  key={index} 
                  evaluation={evaluation} 
                  getScoreColor={getScoreColor}
                  getScoreBgColor={getScoreBgColor}
                  getRiskColor={getRiskColor}
                  getActionColor={getActionColor}
                />
              ))}
            </div>
          </div>
        )}

        {/* Report Metadata */}
        <div className="bg-white rounded-lg shadow p-6 mt-8">
          <div className="flex justify-between text-sm text-gray-600">
            <span>Total Products Evaluated: {report.total_products_evaluated}</span>
            <span>Generated: {new Date(report.generated_at).toLocaleString()}</span>
          </div>
        </div>
      </main>
    </div>
  );
}

function ProductCard({ evaluation, getScoreColor, getScoreBgColor, getRiskColor, getActionColor }) {
  const { product, pop_relevance_score, risk_assessment, suggested_action, reasoning, confidence_score } = evaluation;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900">{product.name}</h3>
          <p className="text-sm text-gray-600 mt-1">{product.description}</p>
          <div className="flex flex-wrap gap-2 mt-2">
            <span className="px-2 py-1 bg-gray-100 text-xs rounded text-gray-700">
              {product.category}
            </span>
            <span className="px-2 py-1 bg-gray-100 text-xs rounded text-gray-700">
              Source: {product.source}
            </span>
          </div>
        </div>
        <div className="text-right ml-4">
          <div className={`px-3 py-1 rounded-lg ${getScoreBgColor(pop_relevance_score)}`}>
            <span className={`text-lg font-bold ${getScoreColor(pop_relevance_score)}`}>
              {pop_relevance_score.toFixed(1)}
            </span>
          </div>
          <p className="text-xs text-gray-600 mt-1">PoP Score</p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <div>
          <p className="text-xs text-gray-600">Trend Score</p>
          <p className="text-sm font-semibold">{product.trend_score}</p>
        </div>
        <div>
          <p className="text-xs text-gray-600">Market Growth</p>
          <p className="text-sm font-semibold">{product.market_growth_rate}%</p>
        </div>
        <div>
          <p className="text-xs text-gray-600">Consumer Interest</p>
          <p className="text-sm font-semibold">{product.consumer_interest_score}</p>
        </div>
        <div>
          <p className="text-xs text-gray-600">Confidence</p>
          <p className="text-sm font-semibold">{confidence_score.toFixed(0)}%</p>
        </div>
      </div>

      <div className="mb-4">
        <p className="text-xs text-gray-600 mb-2">Risk Assessment</p>
        <div className="flex flex-wrap gap-2">
          <span className={`px-2 py-1 text-xs rounded ${getRiskColor(risk_assessment.tariff_risk)}`}>
            Tariff: {risk_assessment.tariff_risk}
          </span>
          <span className={`px-2 py-1 text-xs rounded ${getRiskColor(risk_assessment.fda_concern)}`}>
            FDA: {risk_assessment.fda_concern}
          </span>
          <span className={`px-2 py-1 text-xs rounded ${getRiskColor(risk_assessment.supply_chain_risk)}`}>
            Supply: {risk_assessment.supply_chain_risk}
          </span>
          <span className={`px-2 py-1 text-xs rounded ${getRiskColor(risk_assessment.competition_risk)}`}>
            Competition: {risk_assessment.competition_risk}
          </span>
        </div>
        {risk_assessment.flags.length > 0 && (
          <div className="mt-2">
            <p className="text-xs text-gray-600 mb-1">Flags:</p>
            <div className="flex flex-wrap gap-1">
              {risk_assessment.flags.map((flag, index) => (
                <span key={index} className="px-2 py-1 bg-red-100 text-xs rounded text-red-700">
                  {flag}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="flex justify-between items-center">
        <div className="flex-1">
          <span className={`px-3 py-1 text-sm rounded-full font-medium ${getActionColor(suggested_action)}`}>
            {suggested_action}
          </span>
        </div>
        <div className="text-right ml-4">
          <p className="text-xs text-gray-600">Reasoning</p>
          <p className="text-sm text-gray-700">{reasoning}</p>
        </div>
      </div>
    </div>
  );
}
