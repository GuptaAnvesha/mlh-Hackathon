import React, { useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  Linking,
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { API_BASE_URL } from "./config";

const VERDICT_STYLE = {
  SUPPORTED: { color: "#22c55e", label: "Supported" },
  DISPUTED: { color: "#ef4444", label: "Disputed" },
  MISLEADING: { color: "#f59e0b", label: "Misleading" },
  UNSUPPORTED: { color: "#94a3b8", label: "Unsupported" },
  OPINION: { color: "#60a5fa", label: "Opinion" },
};

const SAMPLE =
  "The Great Wall of China is the only man-made object visible from space " +
  "with the naked eye. It was built in a single dynasty and is over 20,000 " +
  "km long. Honey never spoils.";

function scoreColor(score) {
  if (score >= 75) return "#22c55e";
  if (score >= 45) return "#f59e0b";
  return "#ef4444";
}

function ClaimCard({ item }) {
  const style = VERDICT_STYLE[item.verdict] || VERDICT_STYLE.UNSUPPORTED;
  return (
    <View style={styles.card}>
      <View style={styles.cardHeader}>
        <View style={[styles.badge, { backgroundColor: style.color + "22", borderColor: style.color }]}>
          <Text style={[styles.badgeText, { color: style.color }]}>{style.label}</Text>
        </View>
        <Text style={styles.confidence}>{Math.round(item.confidence * 100)}%</Text>
      </View>
      <Text style={styles.claimText}>{item.claim}</Text>
      <Text style={styles.explanation}>{item.explanation}</Text>
      {item.citations?.slice(0, 3).map((c, i) => (
        <TouchableOpacity key={i} onPress={() => c.uri && Linking.openURL(c.uri)}>
          <Text style={styles.citation} numberOfLines={1}>
            🔗 {c.title || c.uri}
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  );
}

export default function App() {
  const [text, setText] = useState(SAMPLE);
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);

  async function analyze() {
    setLoading(true);
    setError(null);
    setReport(null);
    try {
      const res = await fetch(`${API_BASE_URL}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail.detail || `Server error ${res.status}`);
      }
      setReport(await res.json());
    } catch (e) {
      setError(e.message || "Could not reach the backend. Check config.js.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar barStyle="light-content" />
      <FlatList
        contentContainerStyle={styles.container}
        data={report?.results || []}
        keyExtractor={(_, i) => String(i)}
        renderItem={ClaimCard}
        ListHeaderComponent={
          <View>
            <Text style={styles.title}>Veritas</Text>
            <Text style={styles.subtitle}>Grounded fact-checking, powered by Gemini</Text>

            <TextInput
              style={styles.input}
              multiline
              placeholder="Paste an article, tweet, or claim to fact-check…"
              placeholderTextColor="#64748b"
              value={text}
              onChangeText={setText}
            />

            <TouchableOpacity
              style={[styles.button, loading && styles.buttonDisabled]}
              onPress={analyze}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator color="#0b1020" />
              ) : (
                <Text style={styles.buttonText}>Check the facts</Text>
              )}
            </TouchableOpacity>

            {error && <Text style={styles.error}>⚠️ {error}</Text>}

            {report && (
              <View style={styles.scoreBox}>
                <Text style={[styles.score, { color: scoreColor(report.credibility_score) }]}>
                  {report.credibility_score}
                  <Text style={styles.scoreMax}>/100</Text>
                </Text>
                <Text style={styles.summary}>{report.summary}</Text>
              </View>
            )}
          </View>
        }
        ListEmptyComponent={
          loading ? (
            <Text style={styles.hint}>Searching the web and grounding each claim…</Text>
          ) : null
        }
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: "#0b1020" },
  container: { padding: 20, paddingBottom: 60 },
  title: { fontSize: 40, fontWeight: "800", color: "#f8fafc", letterSpacing: -1 },
  subtitle: { fontSize: 15, color: "#94a3b8", marginBottom: 20 },
  input: {
    minHeight: 120,
    backgroundColor: "#141b30",
    borderRadius: 16,
    borderWidth: 1,
    borderColor: "#243049",
    color: "#e2e8f0",
    padding: 16,
    fontSize: 16,
    textAlignVertical: "top",
  },
  button: {
    backgroundColor: "#38bdf8",
    borderRadius: 14,
    padding: 16,
    alignItems: "center",
    marginTop: 14,
  },
  buttonDisabled: { opacity: 0.6 },
  buttonText: { color: "#0b1020", fontSize: 17, fontWeight: "700" },
  error: { color: "#f87171", marginTop: 14 },
  hint: { color: "#64748b", textAlign: "center", marginTop: 30 },
  scoreBox: { alignItems: "center", marginTop: 24, marginBottom: 8 },
  score: { fontSize: 64, fontWeight: "800" },
  scoreMax: { fontSize: 24, color: "#475569", fontWeight: "600" },
  summary: { color: "#cbd5e1", textAlign: "center", marginTop: 4, fontSize: 14 },
  card: {
    backgroundColor: "#141b30",
    borderRadius: 16,
    padding: 16,
    marginTop: 14,
    borderWidth: 1,
    borderColor: "#243049",
  },
  cardHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  badge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 999, borderWidth: 1 },
  badgeText: { fontSize: 12, fontWeight: "700" },
  confidence: { color: "#64748b", fontSize: 13, fontWeight: "600" },
  claimText: { color: "#f1f5f9", fontSize: 16, fontWeight: "600", marginTop: 10 },
  explanation: { color: "#94a3b8", fontSize: 14, marginTop: 6, lineHeight: 20 },
  citation: { color: "#38bdf8", fontSize: 13, marginTop: 8 },
});
