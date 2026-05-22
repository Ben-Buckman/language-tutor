import React, { useState, useRef, useEffect } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  StyleSheet,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from "react-native";
import * as Speech from "expo-speech";
import { API_BASE, Language, getLangConfig } from "../constants";

type Message = { role: "user" | "assistant"; content: string };

export default function ConversationScreen({ language }: { language: Language }) {
  const langConfig = getLangConfig(language);
  const [history, setHistory] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [speakingId, setSpeakingId] = useState<number | null>(null);
  const [bestVoice, setBestVoice] = useState<string | undefined>();
  const listRef = useRef<FlatList>(null);

  useEffect(() => {
    Speech.getAvailableVoicesAsync()
      .then((voices) => {
        const prefix = langConfig.ttsCode.split("-")[0].toLowerCase();
        const matching = voices.filter((v) => v.language.toLowerCase().startsWith(prefix));
        const enhanced = matching.filter((v) => v.quality === Speech.VoiceQuality.Enhanced);
        setBestVoice((enhanced[0] ?? matching[0])?.identifier);
      })
      .catch(() => {});
  }, [language]);

  function speakMessage(text: string, index: number) {
    if (speakingId === index) {
      Speech.stop();
      setSpeakingId(null);
      return;
    }
    Speech.stop();
    setSpeakingId(index);
    Speech.speak(text, {
      language: langConfig.ttsCode,
      voice: bestVoice,
      onDone: () => setSpeakingId(null),
      onError: () => setSpeakingId(null),
    });
  }

  async function send() {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    setLoading(true);

    const optimisticHistory: Message[] = [...history, { role: "user", content: text }];
    setHistory(optimisticHistory);

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_input: text, history }),
      });
      const data = await res.json();
      setHistory(data.history);
    } catch {
      setHistory([...optimisticHistory, { role: "assistant", content: "(error — could not reach server)" }]);
    } finally {
      setLoading(false);
      setTimeout(() => listRef.current?.scrollToEnd({ animated: true }), 100);
    }
  }

  function renderBubble({ item, index }: { item: Message; index: number }) {
    const isUser = item.role === "user";
    const isSpeaking = speakingId === index;
    return (
      <View style={[styles.bubble, isUser ? styles.userBubble : styles.aiBubble]}>
        <Text style={[styles.bubbleText, isUser ? styles.userText : styles.aiText]}>
          {item.content}
        </Text>
        <TouchableOpacity style={styles.speakBtn} onPress={() => speakMessage(item.content, index)}>
          <Text style={[styles.speakIcon, isSpeaking && styles.speakIconActive]}>
            {isSpeaking ? "⏹" : "🔊"}
          </Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
      keyboardVerticalOffset={90}
    >
      <FlatList
        ref={listRef}
        data={history}
        keyExtractor={(_, i) => String(i)}
        renderItem={renderBubble}
        contentContainerStyle={styles.list}
        onContentSizeChange={() => listRef.current?.scrollToEnd({ animated: true })}
      />

      {loading && (
        <View style={styles.loadingRow}>
          <ActivityIndicator size="small" color="#666" />
          <Text style={styles.loadingText}>thinking...</Text>
        </View>
      )}

      <View style={styles.inputRow}>
        <TextInput
          style={styles.input}
          value={input}
          onChangeText={setInput}
          placeholder="Ask anything..."
          placeholderTextColor="#999"
          onSubmitEditing={send}
          returnKeyType="send"
          editable={!loading}
          multiline
        />
        <TouchableOpacity style={styles.sendButton} onPress={send} disabled={loading}>
          <Text style={styles.sendText}>Send</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f5f5f5" },
  list: { padding: 12, paddingBottom: 4 },
  bubble: {
    maxWidth: "80%",
    marginVertical: 4,
    padding: 12,
    borderRadius: 16,
  },
  userBubble: {
    alignSelf: "flex-end",
    backgroundColor: "#007AFF",
    borderBottomRightRadius: 4,
  },
  aiBubble: {
    alignSelf: "flex-start",
    backgroundColor: "#fff",
    borderBottomLeftRadius: 4,
    shadowColor: "#000",
    shadowOpacity: 0.06,
    shadowRadius: 4,
    elevation: 2,
  },
  bubbleText: { fontSize: 16, lineHeight: 22 },
  userText: { color: "#fff" },
  aiText: { color: "#111" },
  speakBtn: { marginTop: 6, alignSelf: "flex-end" },
  speakIcon: { fontSize: 14, opacity: 0.6 },
  speakIconActive: { opacity: 1 },
  loadingRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingVertical: 6,
    gap: 8,
  },
  loadingText: { color: "#666", fontSize: 13 },
  inputRow: {
    flexDirection: "row",
    padding: 10,
    backgroundColor: "#fff",
    borderTopWidth: 1,
    borderTopColor: "#e0e0e0",
    gap: 8,
    alignItems: "flex-end",
  },
  input: {
    flex: 1,
    backgroundColor: "#f0f0f0",
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    fontSize: 16,
    maxHeight: 120,
  },
  sendButton: {
    backgroundColor: "#007AFF",
    borderRadius: 20,
    paddingHorizontal: 18,
    paddingVertical: 10,
    justifyContent: "center",
  },
  sendText: { color: "#fff", fontWeight: "600", fontSize: 15 },
});
