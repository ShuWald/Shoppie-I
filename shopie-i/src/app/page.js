"use client";



import { useState, useEffect } from "react";

import Sidebar from "../components/Sidebar";



export default function Home() {

  const [report, setReport] = useState(null);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState(null);

  const [activeTab, setActiveTab] = useState("overview");



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
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      
      {/* Main Content */}
      <div className="flex-1">
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

        {/* Tab Content */}
        {activeTab === "overview" && (
          <div>
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
          </div>
        )}

        {activeTab === "products" && (
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-6">All Products</h2>
            <div className="space-y-4">
              {/* High Priority Products */}
              {report.high_priority_products.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    High Priority Opportunities ({report.high_priority_products.length})
                  </h3>
                  {report.high_priority_products.map((evaluation, index) => (
                    <ProductCard 
                      key={`high-${index}`} 
                      evaluation={evaluation} 
                      getScoreColor={getScoreColor}
                      getScoreBgColor={getScoreBgColor}
                      getRiskColor={getRiskColor}
                      getActionColor={getActionColor}
                    />
                  ))}
                </div>
              )}

              {/* Medium Priority Products */}
              {report.medium_priority_products.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Medium Priority Considerations ({report.medium_priority_products.length})
                  </h3>
                  {report.medium_priority_products.map((evaluation, index) => (
                    <ProductCard 
                      key={`med-${index}`} 
                      evaluation={evaluation} 
                      getScoreColor={getScoreColor}
                      getScoreBgColor={getScoreBgColor}
                      getRiskColor={getRiskColor}
                      getActionColor={getActionColor}
                    />
                  ))}
                </div>
              )}

              {/* Low Priority Products */}
              {report.low_priority_products.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Low Priority ({report.low_priority_products.length})
                  </h3>
                  {report.low_priority_products.map((evaluation, index) => (
                    <ProductCard 
                      key={`low-${index}`} 
                      evaluation={evaluation} 
                      getScoreColor={getScoreColor}
                      getScoreBgColor={getScoreBgColor}
                      getRiskColor={getRiskColor}
                      getActionColor={getActionColor}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === "visual" && (
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-6">Visual Data Analysis</h2>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* POP RELEVANCE SCORES BY PRODUCT - Horizontal Bar Chart */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">POP RELEVANCE SCORES BY PRODUCT</h3>
                <div className="space-y-3">
                  {report.high_priority_products.map((evaluation, index) => (
                    <div key={index} className="flex items-center">
                      <div className="w-32 text-sm text-gray-600 truncate">{evaluation.product.name}</div>
                      <div className="flex-1 mx-3">
                        <div className="bg-gray-200 rounded-full h-6 relative">
                          <div 
                            className="bg-green-500 h-6 rounded-full flex items-center justify-end pr-2"
                            style={{width: `${evaluation.pop_relevance_score}%`}}
                          >
                            <span className="text-xs text-white font-semibold">{evaluation.pop_relevance_score.toFixed(1)}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                  {report.medium_priority_products.map((evaluation, index) => (
                    <div key={`med-${index}`} className="flex items-center">
                      <div className="w-32 text-sm text-gray-600 truncate">{evaluation.product.name}</div>
                      <div className="flex-1 mx-3">
                        <div className="bg-gray-200 rounded-full h-6 relative">
                          <div 
                            className="bg-yellow-500 h-6 rounded-full flex items-center justify-end pr-2"
                            style={{width: `${evaluation.pop_relevance_score}%`}}
                          >
                            <span className="text-xs text-white font-semibold">{evaluation.pop_relevance_score.toFixed(1)}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                  {report.low_priority_products.filter(p => p.pop_relevance_score >= 50).map((evaluation, index) => (
                    <div key={`low-${index}`} className="flex items-center">
                      <div className="w-32 text-sm text-gray-600 truncate">{evaluation.product.name}</div>
                      <div className="flex-1 mx-3">
                        <div className="bg-gray-200 rounded-full h-6 relative">
                          <div 
                            className="bg-orange-500 h-6 rounded-full flex items-center justify-end pr-2"
                            style={{width: `${evaluation.pop_relevance_score}%`}}
                          >
                            <span className="text-xs text-white font-semibold">{evaluation.pop_relevance_score.toFixed(1)}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="flex justify-center space-x-6 mt-4">
                  <div className="flex items-center">
                    <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                    <span className="text-xs text-gray-600">High Priority</span>
                  </div>
                  <div className="flex items-center">
                    <div className="w-3 h-3 bg-yellow-500 rounded-full mr-2"></div>
                    <span className="text-xs text-gray-600">Medium Priority</span>
                  </div>
                  <div className="flex items-center">
                    <div className="w-3 h-3 bg-orange-500 rounded-full mr-2"></div>
                    <span className="text-xs text-gray-600">Needs Development</span>
                  </div>
                </div>
              </div>

              {/* CATEGORY DISTRIBUTION - Donut Chart */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">CATEGORY DISTRIBUTION</h3>
                <div className="flex items-center justify-center">
                  <div className="relative w-48 h-48">
                    {/* Simple donut chart using CSS */}
                    <div className="absolute inset-0 rounded-full border-8 border-blue-500 border-r-transparent border-b-transparent transform rotate-45"></div>
                    <div className="absolute inset-0 rounded-full border-8 border-green-500 border-l-transparent border-b-transparent transform -rotate-45"></div>
                    <div className="absolute inset-0 rounded-full border-8 border-yellow-500 border-t-transparent border-r-transparent transform rotate-12"></div>
                    <div className="absolute inset-0 rounded-full border-8 border-purple-500 border-l-transparent border-t-transparent transform -rotate-12"></div>
                    <div className="absolute inset-8 bg-white rounded-full flex items-center justify-center">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-gray-900">{report.total_products_evaluated}</div>
                        <div className="text-xs text-gray-600">Total</div>
                      </div>
                    </div>
                  </div>
                  <div className="ml-8 space-y-2">
                    <div className="flex items-center">
                      <div className="w-3 h-3 bg-blue-500 rounded-full mr-2"></div>
                      <span className="text-sm text-gray-700">Herbal supplement</span>
                    </div>
                    <div className="flex items-center">
                      <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                      <span className="text-sm text-gray-700">Beverage</span>
                    </div>
                    <div className="flex items-center">
                      <div className="w-3 h-3 bg-yellow-500 rounded-full mr-2"></div>
                      <span className="text-sm text-gray-700">Functional food</span>
                    </div>
                    <div className="flex items-center">
                      <div className="w-3 h-3 bg-purple-500 rounded-full mr-2"></div>
                      <span className="text-sm text-gray-700">Topical</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* MARKET GROWTH VS CONSUMER INTEREST - Scatter Plot */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">MARKET GROWTH VS CONSUMER INTEREST</h3>
                <div className="relative h-64 bg-gray-50 rounded-lg p-4">
                  <div className="absolute bottom-0 left-0 w-full h-px bg-gray-300"></div>
                  <div className="absolute top-0 left-0 w-full h-px bg-gray-300"></div>
                  <div className="absolute bottom-0 left-0 h-full w-px bg-gray-300"></div>
                  <div className="absolute bottom-0 right-0 h-full w-px bg-gray-300"></div>
                  
                  {/* Plot points */}
                  {[...report.high_priority_products, ...report.medium_priority_products, ...report.low_priority_products].map((evaluation, index) => (
                    <div
                      key={index}
                      className={`absolute w-3 h-3 rounded-full transform -translate-x-1/2 -translate-y-1/2 ${
                        evaluation.pop_relevance_score >= 75 ? 'bg-green-500' :
                        evaluation.pop_relevance_score >= 60 ? 'bg-yellow-500' : 'bg-orange-500'
                      }`}
                      style={{
                        left: `${evaluation.product.market_growth_rate}%`,
                        bottom: `${evaluation.product.consumer_interest_score}%`
                      }}
                      title={`${evaluation.product.name}: Growth ${evaluation.product.market_growth_rate}%, Interest ${evaluation.product.consumer_interest_score}%`}
                    ></div>
                  ))}
                  
                  {/* Axis labels */}
                  <div className="absolute bottom-2 left-2 text-xs text-gray-600">0</div>
                  <div className="absolute bottom-2 right-2 text-xs text-gray-600">100%</div>
                  <div className="absolute top-2 left-2 text-xs text-gray-600">100%</div>
                  <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 text-xs text-gray-600 -mb-4">Market Growth</div>
                  <div className="absolute left-0 top-1/2 transform -translate-y-1/2 -rotate-90 text-xs text-gray-600 -ml-8">Consumer Interest</div>
                </div>
              </div>

              {/* RISK PROFILE BREAKDOWN - Stacked Bar Chart */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">RISK PROFILE BREAKDOWN</h3>
                <div className="space-y-3">
                  {['Tariff', 'FDA', 'Supply', 'Competition'].map((riskType, index) => {
                    const lowCount = [...report.high_priority_products, ...report.medium_priority_products, ...report.low_priority_products]
                      .filter(p => {
                        const risk = p.risk_assessment;
                        if (riskType === 'Tariff') return risk.tariff_risk === 'low';
                        if (riskType === 'FDA') return risk.fda_concern === 'low';
                        if (riskType === 'Supply') return risk.supply_chain_risk === 'low';
                        if (riskType === 'Competition') return risk.competition_risk === 'low';
                        return false;
                      }).length;
                    
                    const mediumCount = [...report.high_priority_products, ...report.medium_priority_products, ...report.low_priority_products]
                      .filter(p => {
                        const risk = p.risk_assessment;
                        if (riskType === 'Tariff') return risk.tariff_risk === 'medium';
                        if (riskType === 'FDA') return risk.fda_concern === 'medium';
                        if (riskType === 'Supply') return risk.supply_chain_risk === 'medium';
                        if (riskType === 'Competition') return risk.competition_risk === 'medium';
                        return false;
                      }).length;
                    
                    const highCount = [...report.high_priority_products, ...report.medium_priority_products, ...report.low_priority_products]
                      .filter(p => {
                        const risk = p.risk_assessment;
                        if (riskType === 'Tariff') return risk.tariff_risk === 'high';
                        if (riskType === 'FDA') return risk.fda_concern === 'high';
                        if (riskType === 'Supply') return risk.supply_chain_risk === 'high';
                        if (riskType === 'Competition') return risk.competition_risk === 'high';
                        return false;
                      }).length;
                    
                    const total = lowCount + mediumCount + highCount;
                    
                    return (
                      <div key={index} className="flex items-center">
                        <div className="w-20 text-sm text-gray-600">{riskType}</div>
                        <div className="flex-1 mx-3">
                          <div className="bg-gray-200 rounded-full h-6 flex">
                            {lowCount > 0 && (
                              <div 
                                className="bg-green-500 h-6 rounded-l-full flex items-center justify-center"
                                style={{width: `${(lowCount/total)*100}%`}}
                              >
                                {lowCount > 0 && <span className="text-xs text-white">{lowCount}</span>}
                              </div>
                            )}
                            {mediumCount > 0 && (
                              <div 
                                className="bg-yellow-500 h-6 flex items-center justify-center"
                                style={{width: `${(mediumCount/total)*100}%`}}
                              >
                                <span className="text-xs text-white">{mediumCount}</span>
                              </div>
                            )}
                            {highCount > 0 && (
                              <div 
                                className="bg-red-500 h-6 rounded-r-full flex items-center justify-center"
                                style={{width: `${(highCount/total)*100}%`}}
                              >
                                <span className="text-xs text-white">{highCount}</span>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
                <div className="flex justify-center space-x-6 mt-4">
                  <div className="flex items-center">
                    <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                    <span className="text-xs text-gray-600">Low Risk</span>
                  </div>
                  <div className="flex items-center">
                    <div className="w-3 h-3 bg-yellow-500 rounded-full mr-2"></div>
                    <span className="text-xs text-gray-600">Medium Risk</span>
                  </div>
                  <div className="flex items-center">
                    <div className="w-3 h-3 bg-red-500 rounded-full mr-2"></div>
                    <span className="text-xs text-gray-600">High Risk</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "trends" && (
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-6">Trend Predictions</h2>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Emerging Trends Analysis</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  <div className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center mb-2">
                      <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center mr-3">
                        <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                        </svg>
                      </div>
                      <h4 className="font-semibold text-gray-900">Herbal Supplements</h4>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">Strong upward trend with 85% market confidence</p>
                    <div className="flex items-center text-xs text-green-600">
                      <span className="font-medium">+24% growth expected</span>
                    </div>
                  </div>
                  
                  <div className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center mb-2">
                      <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center mr-3">
                        <svg className="w-4 h-4 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M12 5l7 7-7 7" />
                        </svg>
                      </div>
                      <h4 className="font-semibold text-gray-900">Functional Beverages</h4>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">Moderate growth with seasonal variations</p>
                    <div className="flex items-center text-xs text-yellow-600">
                      <span className="font-medium">+12% growth expected</span>
                    </div>
                  </div>
                  
                  <div className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center mb-2">
                      <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mr-3">
                        <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                        </svg>
                      </div>
                      <h4 className="font-semibold text-gray-900">Topical Products</h4>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">Steady demand with niche opportunities</p>
                    <div className="flex items-center text-xs text-blue-600">
                      <span className="font-medium">+8% growth expected</span>
                    </div>
                  </div>
                </div>
              </div>
              
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Seasonal Forecast</h3>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700">Q1 2026</span>
                      <div className="flex items-center">
                        <div className="w-32 bg-gray-200 rounded-full h-2 mr-3">
                          <div className="bg-blue-500 h-2 rounded-full" style={{width: "65%"}}></div>
                        </div>
                        <span className="text-sm text-gray-600">High demand</span>
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700">Q2 2026</span>
                      <div className="flex items-center">
                        <div className="w-32 bg-gray-200 rounded-full h-2 mr-3">
                          <div className="bg-green-500 h-2 rounded-full" style={{width: "85%"}}></div>
                        </div>
                        <span className="text-sm text-gray-600">Peak season</span>
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700">Q3 2026</span>
                      <div className="flex items-center">
                        <div className="w-32 bg-gray-200 rounded-full h-2 mr-3">
                          <div className="bg-yellow-500 h-2 rounded-full" style={{width: "70%"}}></div>
                        </div>
                        <span className="text-sm text-gray-600">Moderate</span>
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700">Q4 2026</span>
                      <div className="flex items-center">
                        <div className="w-32 bg-gray-200 rounded-full h-2 mr-3">
                          <div className="bg-purple-500 h-2 rounded-full" style={{width: "90%"}}></div>
                        </div>
                        <span className="text-sm text-gray-600">Holiday peak</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
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

