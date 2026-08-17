import { Component, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { NgxChessBoardModule, NgxChessBoardView } from 'ngx-chess-board';
import { ChessApiService } from './chess-api.service';

/**
 * Composant principal : échiquier interactif + panneau de recommandations.
 * À chaque coup joué, on récupère le FEN et on interroge le backend
 * (coups théoriques, évaluation Stockfish, contexte RAG, vidéos).
 */
@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, NgxChessBoardModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss',
})
export class AppComponent {
  @ViewChild('board', { static: false }) board!: NgxChessBoardView;

  fen = 'Position de départ';
  loading = false;
  error: string | null = null;

  moves: any[] = [];
  movesSource = '';
  evaluation: any = null;
  openingName = '';
  ragResults: any[] = [];
  videos: any[] = [];

  constructor(
    private api: ChessApiService,
    private sanitizer: DomSanitizer,
  ) {}

  /** Déclenché par ngx-chess-board à chaque coup. */
  onMove(event: any): void {
    const fen = event?.fen;
    if (!fen) return;
    this.analyze(fen);
  }

  /** Interroge le backend pour la position courante. */
  analyze(fen: string): void {
    this.fen = fen;
    this.loading = true;
    this.error = null;
    this.ragResults = [];
    this.videos = [];
    this.openingName = '';

    // 1. Coups théoriques (Lichess + fallback)
    this.api.getMoves(fen).subscribe({
      next: (res) => {
        this.moves = res.moves ?? [];
        this.movesSource = res.source ?? '';
        const name = res.opening?.name;
        if (name) {
          this.openingName = name;
          this.loadContext(name);
        }
        this.loading = false;
      },
      error: () => {
        this.moves = [];
        this.loading = false;
      },
    });

    // 2. Évaluation Stockfish (en parallèle)
    this.api.evaluate(fen).subscribe({
      next: (res) => (this.evaluation = res),
      error: () => (this.evaluation = null),
    });
  }

  /** Contexte RAG + vidéos pour l'ouverture identifiée. */
  private loadContext(opening: string): void {
    this.api.vectorSearch(opening).subscribe({
      next: (res) => (this.ragResults = res.results ?? []),
      error: () => (this.ragResults = []),
    });
    this.api.getVideos(opening).subscribe({
      next: (res) => (this.videos = res.videos ?? []),
      error: () => (this.videos = []),
    });
  }

  /** Formate le score Stockfish pour l'affichage. */
  formatEval(): string {
    if (!this.evaluation) return '—';
    if (this.evaluation.eval_type === 'mate') {
      return `Mat en ${Math.abs(this.evaluation.value)}`;
    }
    const pawns = (this.evaluation.value / 100).toFixed(2);
    return `${this.evaluation.value > 0 ? '+' : ''}${pawns}`;
  }

  reset(): void {
    this.board.reset();
    this.moves = [];
    this.evaluation = null;
    this.ragResults = [];
    this.videos = [];
    this.openingName = '';
    this.fen = 'Position de départ';
  }

  safeEmbed(url: string): SafeResourceUrl {
    return this.sanitizer.bypassSecurityTrustResourceUrl(url);
  }
}
