import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

/**
 * Service d'accès au backend FastAPI.
 * L'URL de base est relative (/api/v1) : en production, nginx (conteneur front)
 * proxifie /api vers le service backend. Pas de CORS, pas d'hôte en dur.
 */
@Injectable({ providedIn: 'root' })
export class ChessApiService {
  private readonly base = '/api/v1';

  constructor(private http: HttpClient) {}

  getMoves(fen: string): Observable<any> {
    return this.http.get(`${this.base}/moves/${encodeURIComponent(fen)}`);
  }

  evaluate(fen: string): Observable<any> {
    return this.http.get(`${this.base}/evaluate/${encodeURIComponent(fen)}`);
  }

  vectorSearch(query: string, k = 3): Observable<any> {
    return this.http.get(`${this.base}/vector-search`, { params: { query, k } });
  }

  getVideos(opening: string): Observable<any> {
    return this.http.get(`${this.base}/videos/${encodeURIComponent(opening)}`);
  }
}
