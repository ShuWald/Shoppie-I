// Test the parseInsightCard function logic
const parseInsightCard = (insight) => {
  // Distribute Existing: 2
  if (insight.includes("Distribute Existing")) {
    const match = insight.match(/Distribute Existing: (\d+)/);
    return {
      title: "Ready to Distribute",
      value: match ? match[1] : "0",
      subtitle: "products ready for market",
      valueClass: "text-2xl font-bold text-blue-600"
    };
  }

  // Develop New: 5
  if (insight.includes("Develop New")) {
    const match = insight.match(/Develop New: (\d+)/);
    return {
      title: "Development Pipeline",
      value: match ? match[1] : "0", 
      subtitle: "products requiring development",
      valueClass: "text-2xl font-bold text-purple-600"
    };
  }

  // Default fallback
  return {
    title: "Insight",
    value: insight,
    subtitle: "data point",
    valueClass: "text-base font-bold"
  };
};

// Test with sample data
const testInsights = [
  "Distribute Existing: 2",
  "Develop New: 5",
  "Average PoP relevance score: 67.1"
];

console.log("Testing parseInsightCard function:");
testInsights.forEach((insight, index) => {
  const cardData = parseInsightCard(insight);
  console.log(`${index + 1}. Insight: "${insight}"`);
  console.log(`   Title: ${cardData.title}`);
  console.log(`   Value: ${cardData.value}`);
  console.log(`   Subtitle: ${cardData.subtitle}`);
  console.log(`   ValueClass: ${cardData.valueClass}`);
  console.log("---");
});
