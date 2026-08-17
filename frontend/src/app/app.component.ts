import { Component, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { NgxChessBoardModule, NgxChessBoardView } from 'ngx-chess-board';
import { ChessApiService } from './chess-api.service';

/**
 * Composant principal : échiquier interactif + panneau de recommandations.
 * À chaque coup, on appelle l'agent LangGraph (un seul endpoint) qui orchestre
 * tous les outils et renvoie une réponse unifiée, dont une synthèse en langage
 * naturel.
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

  synthesis = '';
  synthesisSource = '';
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

  /** Appel unique à l'agent LangGraph. */
  analyze(fen: string): void {
    this.fen = fen;
    this.loading = true;

    this.api.analyze(fen).subscribe({
      next: (res) => {
        this.synthesis = res.synthesis ?? '';
        this.synthesisSource = res.synthesis_source ?? '';
        this.moves = res.moves ?? [];
        this.movesSource = res.moves_source ?? '';
        this.evaluation = res.evaluation ?? null;
        this.openingName = res.opening_name ?? '';
        this.ragResults = res.rag_results ?? [];
        this.videos = res.videos ?? [];
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      },
    });
  }

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
    this.synthesis = '';
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
