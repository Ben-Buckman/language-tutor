import React, { useState, useEffect, useCallback } from "react";
import { NavigationContainer } from "@react-navigation/native";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { Text, View, TouchableOpacity, StyleSheet } from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import ConversationScreen from "./screens/ConversationScreen";
import WordListScreen from "./screens/WordListScreen";
import { DEFAULT_KNOWN_WORDS, LANGUAGES, STORAGE_KEY, Language } from "./constants";
import { WordData, loadWordData, saveWordData } from "./srsStorage";

const Tab = createBottomTabNavigator();

export default function App() {
  const [activeLanguage, setActiveLanguage] = useState<Language>("hebrew");
  const [knownWordsByLang, setKnownWordsByLang] = useState<Record<Language, string[]>>({
    hebrew: [...new Set(DEFAULT_KNOWN_WORDS.hebrew)],
    english: [...new Set(DEFAULT_KNOWN_WORDS.english)],
    spanish: [...new Set(DEFAULT_KNOWN_WORDS.spanish)],
  });
  const [wordDataByLang, setWordDataByLang] = useState<Record<Language, WordData>>({
    hebrew: {},
    english: {},
    spanish: {},
  });

  // Load persisted word lists and SRS data on startup
  useEffect(() => {
    Promise.all(
      LANGUAGES.map(async (lang) => {
        const [wordsJson, srsData] = await Promise.all([
          AsyncStorage.getItem(STORAGE_KEY(lang.id)),
          loadWordData(lang.id),
        ]);
        let words: string[] | null = null;
        if (wordsJson) {
          try {
            const saved: string[] = JSON.parse(wordsJson);
            if (Array.isArray(saved) && saved.length > 0) {
              words = [...new Set(saved)];
            }
          } catch {}
        }
        return { id: lang.id, words, srsData };
      })
    ).then((results) => {
      const wordUpdates: Partial<Record<Language, string[]>> = {};
      const srsUpdates: Partial<Record<Language, WordData>> = {};
      for (const r of results) {
        if (r.words) wordUpdates[r.id] = r.words;
        if (Object.keys(r.srsData).length > 0) srsUpdates[r.id] = r.srsData;
      }
      if (Object.keys(wordUpdates).length > 0) {
        setKnownWordsByLang((prev) => ({ ...prev, ...wordUpdates }));
      }
      if (Object.keys(srsUpdates).length > 0) {
        setWordDataByLang((prev) => ({ ...prev, ...srsUpdates }));
      }
    });
  }, []);

  const updateKnownWords = useCallback((language: Language, words: string[]) => {
    setKnownWordsByLang((prev) => ({ ...prev, [language]: words }));
    AsyncStorage.setItem(STORAGE_KEY(language), JSON.stringify(words));
  }, []);

  const addNewWords = useCallback((language: Language, newWords: string[]) => {
    setKnownWordsByLang((prev) => {
      const merged = [...new Set([...prev[language], ...newWords])];
      AsyncStorage.setItem(STORAGE_KEY(language), JSON.stringify(merged));
      return { ...prev, [language]: merged };
    });
  }, []);

  const updateWordData = useCallback((language: Language, data: WordData) => {
    setWordDataByLang((prev) => ({ ...prev, [language]: data }));
    saveWordData(language, data);
  }, []);

  const knownWords = knownWordsByLang[activeLanguage];
  const wordData = wordDataByLang[activeLanguage];

  const LanguageSelector = () => (
    <View style={styles.langBar}>
      {LANGUAGES.map((lang) => (
        <TouchableOpacity
          key={lang.id}
          style={[styles.langBtn, activeLanguage === lang.id && styles.langBtnActive]}
          onPress={() => setActiveLanguage(lang.id)}
        >
          <Text style={styles.langFlag}>{lang.flag}</Text>
          <Text style={[styles.langLabel, activeLanguage === lang.id && styles.langLabelActive]}>
            {lang.label}
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  );

  return (
    <NavigationContainer>
      <Tab.Navigator
        screenOptions={{
          tabBarActiveTintColor: "#007AFF",
          headerStyle: { backgroundColor: "#fff" },
          headerTitleStyle: { fontWeight: "600" },
        }}
      >
        <Tab.Screen
          name="Chat"
          options={{
            title: "Conversation",
            tabBarIcon: ({ color }) => <Text style={{ fontSize: 20, color }}>💬</Text>,
          }}
        >
          {() => (
            <View style={{ flex: 1 }}>
              <LanguageSelector />
              <ConversationScreen
                key={activeLanguage}
                language={activeLanguage}
              />
            </View>
          )}
        </Tab.Screen>
        <Tab.Screen
          name="Words"
          options={{
            title: "My Words",
            tabBarIcon: ({ color }) => <Text style={{ fontSize: 20, color }}>📖</Text>,
            tabBarBadge: knownWords.length,
          }}
        >
          {() => (
            <View style={{ flex: 1 }}>
              <LanguageSelector />
              <WordListScreen
                language={activeLanguage}
                knownWords={knownWords}
                wordData={wordData}
                onWordsChange={(words) => updateKnownWords(activeLanguage, words)}
              />
            </View>
          )}
        </Tab.Screen>
      </Tab.Navigator>
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  langBar: {
    flexDirection: "row",
    backgroundColor: "#fff",
    borderBottomWidth: 1,
    borderBottomColor: "#e0e0e0",
    paddingVertical: 6,
    paddingHorizontal: 12,
    gap: 8,
  },
  langBtn: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 6,
    paddingHorizontal: 8,
    borderRadius: 10,
    backgroundColor: "#f0f0f0",
    gap: 4,
  },
  langBtnActive: {
    backgroundColor: "#007AFF",
  },
  langFlag: {
    fontSize: 16,
  },
  langLabel: {
    fontSize: 13,
    fontWeight: "500",
    color: "#555",
  },
  langLabelActive: {
    color: "#fff",
  },
});
