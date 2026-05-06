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
  StyleProp,
  TextStyle,
} from "react-native";
import * as Speech from "expo-speech";
import { API_BASE, Language, getLangConfig } from "../constants";
import { WordData } from "../srsStorage";

type Message = { role: "user" | "assistant"; content: string; newWords?: string[] };

export default function ConversationScreen({
  language,
  knownWords,
  wordData,
  onNewWords,
  onWordDataUpdate,
}: {
  language: Language;
  knownWords: string[];
  wordData: WordData;
  onNewWords: (words: string[]) => void;
  onWordDataUpdate: (data: WordData) => void;
}) {
  const langConfig = getLangConfig(language);
  const [history, setHistory] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [knownForms, setKnownForms] = useState<Set<string>>(new Set());
  const [speakingId, setSpeakingId] = useState<number | null>(null);
  const [bestVoice, setBestVoice] = useState<string | undefined>();
  const listRef = useRef<FlatList>(null);

  // Pick the highest-quality available voice for the current language
  useEffect(() => {
    Speech.getAvailableVoicesAsync()
      .then((voices) => {
        const prefix = langConfig.ttsCode.split("-")[0].toLowerCase();
        const matching = voices.filter((v) =>
          v.language.toLowerCase().startsWith(prefix)
        );
        const enhanced = matching.filter(
          (v) => v.quality === Speech.VoiceQuality.Enhanced
        );
        const best = enhanced[0] ?? matching[0];
        setBestVoice(best?.identifier);
      })
      .catch(() => {});
  }, [language]);

  // Fetch the full morphological forms set whenever knownWords changes
  useEffect(() => {
    if (!knownWords.length) return;
    fetch(`${API_BASE}/words/all-forms`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ words: knownWords, language }),
    })
      .then((r) => r.json())
      .then((forms: string[]) => setKnownForms(new Set(forms)))
      .catch(() => {});
  }, [knownWords, language]);

  function extractWords(text: string): string[] {
    let matches: string[] | null;
    if (language === "hebrew") {
      matches = text.match(/[א-ת]+/g);
    } else {
      matches = text.match(/[a-zA-ZÀ-ɏ]+/g);
    }
    return matches ? [...new Set(matches)] : [];
  }

  function isKnown(word: string): boolean {
    if (knownWords.includes(word)) return true;
    if (knownForms.has(word)) return true;
    return false;
  }

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

    // Add any new words the user typed (normalized to lemmas)
    const userWords = extractWords(text);
    const rawNewUserWords = userWords.filter((w) => !isKnown(w));
    let newUserWords = rawNewUserWords;
    if (rawNewUserWords.length) {
      try {
        const lemmaRes = await fetch(`${API_BASE}/words/lemmatize`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ words: rawNewUserWords, language }),
        });
        const lemmas: string[] = await lemmaRes.json();
        newUserWords = [...new Set(lemmas.filter((l) => !isKnown(l)))];
      } catch {}
      if (newUserWords.length) onNewWords(newUserWords);
    }

    const optimisticHistory: Message[] = [
      ...history,
      { role: "user", content: text, newWords: newUserWords.length ? newUserWords : undefined },
    ];
    setHistory(optimisticHistory);

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_input: text,
          history,
          known_words: knownWords,
          language,
          word_data: wordData,
        }),
      });
      const data = await res.json();
      if (data.new_words?.length) {
        onNewWords(data.new_words);
      }
      if (data.word_data) {
        onWordDataUpdate(data.word_data);
      }
      const updatedHistory: Message[] = data.history.map((m: Message, i: number) => {
        if (i === data.history.length - 1 && m.role === "assistant" && data.new_words?.length) {
          return { ...m, newWords: data.new_words };
        }
        if (i === data.history.length - 2 && m.role === "user" && newUserWords.length) {
          return { ...m, newWords: newUserWords };
        }
        return m;
      });
      setHistory(updatedHistory);
    } catch {
      setHistory([
        ...optimisticHistory,
        { role: "assistant", content: "(error — is the server running?)" },
      ]);
    } finally {
      setLoading(false);
      setTimeout(() => listRef.current?.scrollToEnd({ animated: true }), 100);
    }
  }

  function renderBubbleText(content: string, newWords: string[], isUser: boolean) {
    const direction = langConfig.rtl ? "rtl" : "ltr";
    const baseStyle: StyleProp<TextStyle> = [
      styles.bubbleText,
      { writingDirection: direction },
      isUser ? styles.userText : styles.aiText,
    ];

    if (newWords.length > 0) {
      const pattern = new RegExp(
        `(${newWords.map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})`,
        "g"
      );
      const parts = content.split(pattern);
      return (
        <View>
          <TextInput
            editable={false}
            multiline
            scrollEnabled={false}
            value={content}
            style={[baseStyle, { color: "transparent" }]}
          />
          <View pointerEvents="none" style={StyleSheet.absoluteFill}>
            <Text style={baseStyle}>
              {parts.map((part, i) =>
                newWords.includes(part) ? (
                  <Text key={i} style={styles.newWord}>{part}</Text>
                ) : (
                  <Text key={i}>{part}</Text>
                )
              )}
            </Text>
          </View>
        </View>
      );
    }

    return (
      <View>
        <TextInput
          editable={false}
          multiline
          scrollEnabled={false}
          value={content}
          style={[baseStyle, { color: "transparent" }]}
        />
        <View pointerEvents="none" style={StyleSheet.absoluteFill}>
          <Text style={baseStyle}>{content}</Text>
        </View>
      </View>
    );
  }

  function renderBubble({ item, index }: { item: Message; index: number }) {
    const isUser = item.role === "user";
    const isSpeaking = speakingId === index;
    return (
      <View style={[styles.bubble, isUser ? styles.userBubble : styles.aiBubble]}>
        {renderBubbleText(item.content, item.newWords ?? [], isUser)}
        {item.newWords?.length ? (
          <Text style={styles.newWordLabel}>
            +{item.newWords.length} new word{item.newWords.length > 1 ? "s" : ""}:{" "}
            {item.newWords.join(", ")}
          </Text>
        ) : null}
        <TouchableOpacity
          style={styles.speakBtn}
          onPress={() => speakMessage(item.content, index)}
        >
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
          placeholder={`Type in ${langConfig.label}...`}
          placeholderTextColor="#999"
          onSubmitEditing={send}
          returnKeyType="send"
          editable={!loading}
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
  bubbleText: { fontSize: 16, lineHeight: 22, padding: 0 },
  newWord: { backgroundColor: "#FFE066", color: "#111", borderRadius: 3 },
  newWordLabel: { fontSize: 11, color: "#888", marginTop: 6, fontStyle: "italic" },
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
  },
  input: {
    flex: 1,
    backgroundColor: "#f0f0f0",
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    fontSize: 16,
  },
  sendButton: {
    backgroundColor: "#007AFF",
    borderRadius: 20,
    paddingHorizontal: 18,
    justifyContent: "center",
  },
  sendText: { color: "#fff", fontWeight: "600", fontSize: 15 },
});
