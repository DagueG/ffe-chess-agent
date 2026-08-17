import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

/**
 * Service d'accès au backend FastAPI.
 * L'agent LangGraph expose un endpoint unique qui orchestre tous les outils.
 * URL relative (/api/v1) : nginx proxifie vers le backend (pas de CORS).
 */
@Injectable({ providedIn: 'root' })
export class ChessApiService {
  private readonly base = '/api/v1';

  constructor(private http: HttpClient) {}

  /** Analyse complète d'une position par l'agent (coups, éval, RAG, vidéos, synthèse). */
  analyze(fen: string): Observable<any> {
    return this.http.get(`${this.base}/agent/analyze/${encodeURIComponent(fen)}`);
  }
}
