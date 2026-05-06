import AsyncStorage from "@react-native-async-storage/async-storage";
import { Language } from "./constants";

export type WordEntry = {
  exposures: number;
  interval: number;
  due_date: string;
  last_seen: string | null;
};

export type WordData = Record<string, WordEntry>;

const SRS_KEY = (language: Language) => `wordData_${language}`;

export async function loadWordData(language: Language): Promise<WordData> {
  const json = await AsyncStorage.getItem(SRS_KEY(language));
  if (!json) return {};
  try {
    return JSON.parse(json);
  } catch {
    return {};
  }
}

export async function saveWordData(language: Language, data: WordData): Promise<void> {
  await AsyncStorage.setItem(SRS_KEY(language), JSON.stringify(data));
}
