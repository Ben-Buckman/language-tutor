import React, { useState, useCallback } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  StyleSheet,
  Alert,
} from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { API_BASE } from "../constants";
import { WordData } from "../srsStorage";

type WordStat = {
  word: string;
  exposures: number;
  interval: number;
  due_date: string;
  last_seen: string | null;
  due: boolean;
  days_until_due: number;
};

type SortMode = "recent" | "known" | "alpha";

// Max SRS interval from srs.py INTERVALS list
const MAX_INTERVAL = 120;

function knowledgeScore(stat?: WordStat): number {
  if (!stat || stat.exposures === 0) return 0;
  // How strong is the long-term memory trace
  const strength = Math.min(1, stat.interval / MAX_INTERVAL);
  // How much has decayed since due date (if overdue)
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const due = new Date(stat.due_date);
  due.setHours(0, 0, 0, 0);
  const daysOverdue = Math.max(0, (today.getTime() - due.getTime()) / 86400000);
  const decay = Math.exp(-daysOverdue / Math.max(stat.interval, 1));
  return strength * decay;
}

function scoreColor(score: number): string {
  // Red → Orange → Yellow → Green continuous gradient
  if (score <= 0) return "#FF3B30";
  if (score >= 1) return "#34C759";
  // Interpolate hue: 0° (red) → 120° (green) in HSL
  const hue = Math.round(score * 120);
  return `hsl(${hue}, 85%, 45%)`;
}

export default function WordListScreen({
  language,
  knownWords,
  wordData,
  onWordsChange,
}: {
  language: string;
  knownWords: string[];
  wordData: WordData;
  onWordsChange: (words: string[]) => void;
}) {
  const [stats, setStats] = useState<Record<string, WordStat>>({});
  const [search, setSearch] = useState("");
  const [sortMode, setSortMode] = useState<SortMode>("recent");

  useFocusEffect(
    useCallback(() => {
      if (knownWords.length === 0) return;
      fetch(`${API_BASE}/words/stats`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ words: knownWords, language, word_data: wordData }),
      })
        .then((r) => r.json())
        .then((data: WordStat[]) => {
          const map: Record<string, WordStat> = {};
          data.forEach((s) => (map[s.word] = s));
          setStats(map);
        })
        .catch(() => {});
    }, [knownWords, wordData])
  );

  function removeWord(word: string) {
    Alert.alert("Remove word", `Remove "${word}" from your word list?`, [
      { text: "Cancel", style: "cancel" },
      {
        text: "Remove",
        style: "destructive",
        onPress: () => onWordsChange(knownWords.filter((w) => w !== word)),
      },
    ]);
  }

  function resetWords() {
    Alert.alert(
      "Reset word list",
      "Remove ALL words and start from 0? This cannot be undone.",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Reset",
          style: "destructive",
          onPress: () => {
            onWordsChange([]);
            setStats({});
          },
        },
      ]
    );
  }

  function statusLabel(word: string) {
    const s = stats[word];
    if (!s || s.exposures === 0) return "new";
    if (s.due) return "due";
    if (s.days_until_due === 1) return "tmrw";
    return `${s.days_until_due}d`;
  }

  function renderBar(word: string) {
    const score = knowledgeScore(stats[word]);
    const pct = Math.max(2, Math.round(score * 100));
    const color = stats[word]?.exposures === 0 ? "#C7C7CC" : scoreColor(score);
    return (
      <View style={styles.barTrack}>
        <View style={[styles.barFill, { width: `${pct}%` as any, backgroundColor: color }]} />
      </View>
    );
  }

  const uniqueWords = [...new Set(knownWords)];

  const filteredWords = search.trim()
    ? uniqueWords.filter((w) => w.includes(search.trim()))
    : uniqueWords;

  const sortedWords = [...filteredWords].sort((a, b) => {
    if (sortMode === "recent") {
      return uniqueWords.indexOf(b) - uniqueWords.indexOf(a);
    }
    if (sortMode === "known") {
      return knowledgeScore(stats[b]) - knowledgeScore(stats[a]);
    }
    return a.localeCompare(b, language);
  });

  const SORT_OPTIONS: { key: SortMode; label: string }[] = [
    { key: "recent", label: "Recent" },
    { key: "known", label: "Known" },
    { key: "alpha", label: "A–Z" },
  ];

  const dueCount = Object.values(stats).filter((s) => s.due).length;

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.count}>{knownWords.length} words</Text>
        {dueCount > 0 && (
          <Text style={styles.dueCount}>{dueCount} due for review</Text>
        )}
        <TouchableOpacity onPress={resetWords} style={styles.resetButton}>
          <Text style={styles.resetText}>Reset</Text>
        </TouchableOpacity>
      </View>

      {/* Search + Sort */}
      <View style={styles.controlsRow}>
        <TextInput
          style={styles.searchInput}
          value={search}
          onChangeText={setSearch}
          placeholder="Search..."
          placeholderTextColor="#999"
          clearButtonMode="while-editing"
        />
        <View style={styles.sortButtons}>
          {SORT_OPTIONS.map(({ key, label }) => (
            <TouchableOpacity
              key={key}
              style={[styles.sortBtn, sortMode === key && styles.sortBtnActive]}
              onPress={() => setSortMode(key)}
            >
              <Text style={[styles.sortBtnText, sortMode === key && styles.sortBtnTextActive]}>
                {label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      <FlatList
        data={sortedWords}
        keyExtractor={(item, index) => `${item}-${index}`}
        renderItem={({ item }) => (
          <View style={styles.wordRow}>
            <View style={styles.barCol}>
              {renderBar(item)}
            </View>
            <Text style={styles.word}>{item}</Text>
            <Text style={styles.statusLabel}>{statusLabel(item)}</Text>
            <TouchableOpacity onPress={() => removeWord(item)} style={styles.removeButton}>
              <Text style={styles.removeText}>✕</Text>
            </TouchableOpacity>
          </View>
        )}
        contentContainerStyle={styles.list}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f5f5f5" },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  count: { color: "#666", fontSize: 13 },
  dueCount: { color: "#FF3B30", fontSize: 13, fontWeight: "600" },
  resetButton: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#FF3B30",
  },
  resetText: { color: "#FF3B30", fontSize: 12, fontWeight: "600" },
  controlsRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 10,
    paddingVertical: 8,
    gap: 8,
    backgroundColor: "#fff",
    borderBottomWidth: 1,
    borderBottomColor: "#e0e0e0",
  },
  searchInput: {
    flex: 1,
    backgroundColor: "#f0f0f0",
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 8,
    fontSize: 15,
  },
  sortButtons: { flexDirection: "row", gap: 4 },
  sortBtn: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
    backgroundColor: "#f0f0f0",
  },
  sortBtnActive: { backgroundColor: "#007AFF" },
  sortBtnText: { fontSize: 12, color: "#555", fontWeight: "500" },
  sortBtnTextActive: { color: "#fff" },
  list: { padding: 10 },
  wordRow: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#fff",
    padding: 14,
    borderRadius: 10,
    marginBottom: 6,
    shadowColor: "#000",
    shadowOpacity: 0.04,
    shadowRadius: 3,
    elevation: 1,
    gap: 10,
  },
  barCol: { width: 56, justifyContent: "center" },
  barTrack: {
    height: 6,
    backgroundColor: "#E5E5EA",
    borderRadius: 3,
    overflow: "hidden",
  },
  barFill: {
    height: 6,
    borderRadius: 3,
  },
  word: { flex: 1, fontSize: 17, textAlign: "right" },
  statusLabel: { fontSize: 12, color: "#999", minWidth: 36, textAlign: "right" },
  removeButton: { padding: 4 },
  removeText: { color: "#FF3B30", fontSize: 16 },
});
