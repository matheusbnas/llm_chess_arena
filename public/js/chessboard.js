class ChessBoard {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            size: 480,
            showCoordinates: true,
            draggable: true,
            flipped: false,
            ...options
        };
        
        this.board = null;
        this.selectedSquare = null;
        this.possibleMoves = [];
        this.onMoveCallback = null;
        this.onSquareClickCallback = null;
        
        this.pieceSymbols = {
            'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
            'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'
        };
        
        this.init();
    }
    
    init() {
        this.createBoard();
        this.setupEventListeners();
    }
    
    createBoard() {
        this.container.innerHTML = '';
        
        const boardContainer = document.createElement('div');
        boardContainer.className = 'chessboard-container';
        
        const board = document.createElement('div');
        board.className = `chessboard ${this.options.flipped ? 'flipped' : ''}`;
        board.style.width = `${this.options.size}px`;
        board.style.height = `${this.options.size}px`;
        
        // Create squares
        for (let rank = 8; rank >= 1; rank--) {
            for (let file = 0; file < 8; file++) {
                const square = document.createElement('div');
                const fileChar = String.fromCharCode(97 + file); // a-h
                const squareName = `${fileChar}${rank}`;
                
                square.className = `square ${(rank + file) % 2 === 0 ? 'dark' : 'light'}`;
                square.dataset.square = squareName;
                square.dataset.file = fileChar;
                square.dataset.rank = rank;
                
                // Add coordinates
                if (this.options.showCoordinates) {
                    if (file === 7) { // Last file, show rank
                        const rankCoord = document.createElement('div');
                        rankCoord.className = 'coordinates coord-rank';
                        rankCoord.textContent = rank;
                        square.appendChild(rankCoord);
                    }
                    if (rank === 1) { // Last rank, show file
                        const fileCoord = document.createElement('div');
                        fileCoord.className = 'coordinates coord-file';
                        fileCoord.textContent = fileChar;
                        square.appendChild(fileCoord);
                    }
                }
                
                board.appendChild(square);
            }
        }
        
        boardContainer.appendChild(board);
        this.container.appendChild(boardContainer);
        this.board = board;
    }
    
    setupEventListeners() {
        if (!this.options.draggable) return;
        
        this.board.addEventListener('click', (e) => {
            const square = e.target.closest('.square');
            if (!square) return;
            
            this.handleSquareClick(square.dataset.square);
        });
        
        // Drag and drop support
        this.board.addEventListener('dragstart', (e) => {
            if (e.target.classList.contains('piece')) {
                e.dataTransfer.setData('text/plain', e.target.parentElement.dataset.square);
                e.target.classList.add('dragging');
            }
        });
        
        this.board.addEventListener('dragover', (e) => {
            e.preventDefault();
        });
        
        this.board.addEventListener('drop', (e) => {
            e.preventDefault();
            const fromSquare = e.dataTransfer.getData('text/plain');
            const toSquare = e.target.closest('.square')?.dataset.square;
            
            if (fromSquare && toSquare && fromSquare !== toSquare) {
                this.makeMove(fromSquare, toSquare);
            }
            
            // Remove dragging class
            document.querySelectorAll('.piece.dragging').forEach(piece => {
                piece.classList.remove('dragging');
            });
        });
        
        this.board.addEventListener('dragend', (e) => {
            e.target.classList.remove('dragging');
        });
    }
    
    handleSquareClick(squareName) {
        const square = this.getSquareElement(squareName);
        const piece = square.querySelector('.piece');
        
        if (this.selectedSquare) {
            if (this.selectedSquare === squareName) {
                // Deselect
                this.clearSelection();
            } else if (this.possibleMoves.includes(squareName)) {
                // Make move
                this.makeMove(this.selectedSquare, squareName);
                this.clearSelection();
            } else if (piece) {
                // Select new piece
                this.selectSquare(squareName);
            } else {
                this.clearSelection();
            }
        } else if (piece) {
            // Select piece
            this.selectSquare(squareName);
        }
        
        if (this.onSquareClickCallback) {
            this.onSquareClickCallback(squareName, piece?.dataset.piece);
        }
    }
    
    selectSquare(squareName) {
        this.clearSelection();
        this.selectedSquare = squareName;
        
        const square = this.getSquareElement(squareName);
        square.classList.add('selected');
        
        // Get possible moves (this would need to be provided by the chess engine)
        if (this.onGetPossibleMoves) {
            this.possibleMoves = this.onGetPossibleMoves(squareName);
            this.highlightPossibleMoves();
        }
    }
    
    clearSelection() {
        if (this.selectedSquare) {
            const square = this.getSquareElement(this.selectedSquare);
            square.classList.remove('selected');
        }
        
        this.selectedSquare = null;
        this.possibleMoves = [];
        this.clearHighlights();
    }
    
    highlightPossibleMoves() {
        this.possibleMoves.forEach(squareName => {
            const square = this.getSquareElement(squareName);
            const piece = square.querySelector('.piece');
            
            if (piece) {
                square.classList.add('possible-capture');
            } else {
                square.classList.add('possible-move');
            }
        });
    }
    
    clearHighlights() {
        this.board.querySelectorAll('.square').forEach(square => {
            square.classList.remove('possible-move', 'possible-capture', 'highlighted', 'last-move', 'check');
        });
    }
    
    makeMove(fromSquare, toSquare) {
        if (this.onMoveCallback) {
            const move = {
                from: fromSquare,
                to: toSquare,
                promotion: this.getPromotionPiece(fromSquare, toSquare)
            };
            
            this.onMoveCallback(move);
        }
    }
    
    getPromotionPiece(fromSquare, toSquare) {
        const fromElement = this.getSquareElement(fromSquare);
        const piece = fromElement.querySelector('.piece');
        
        if (!piece) return null;
        
        const pieceType = piece.dataset.piece;
        const isWhitePawn = pieceType === 'P';
        const isBlackPawn = pieceType === 'p';
        const toRank = parseInt(toSquare[1]);
        
        if ((isWhitePawn && toRank === 8) || (isBlackPawn && toRank === 1)) {
            return this.showPromotionDialog(pieceType[0] === pieceType[0].toUpperCase());
        }
        
        return null;
    }
    
    showPromotionDialog(isWhite) {
        return new Promise((resolve) => {
            const dialog = document.createElement('div');
            dialog.className = 'promotion-dialog';
            dialog.innerHTML = `
                <h3>Escolha a peça para promoção:</h3>
                <div class="promotion-pieces">
                    <div class="promotion-piece" data-piece="${isWhite ? 'Q' : 'q'}">${isWhite ? '♕' : '♛'}</div>
                    <div class="promotion-piece" data-piece="${isWhite ? 'R' : 'r'}">${isWhite ? '♖' : '♜'}</div>
                    <div class="promotion-piece" data-piece="${isWhite ? 'B' : 'b'}">${isWhite ? '♗' : '♝'}</div>
                    <div class="promotion-piece" data-piece="${isWhite ? 'N' : 'n'}">${isWhite ? '♘' : '♞'}</div>
                </div>
            `;
            
            dialog.addEventListener('click', (e) => {
                if (e.target.classList.contains('promotion-piece')) {
                    const piece = e.target.dataset.piece;
                    document.body.removeChild(dialog);
                    resolve(piece);
                }
            });
            
            document.body.appendChild(dialog);
        });
    }
    
    setPosition(fen) {
        const parts = fen.split(' ');
        const position = parts[0];
        
        // Clear all pieces
        this.board.querySelectorAll('.piece').forEach(piece => piece.remove());
        
        const ranks = position.split('/');
        
        ranks.forEach((rank, rankIndex) => {
            let fileIndex = 0;
            
            for (let char of rank) {
                if (isNaN(char)) {
                    // It's a piece
                    const squareName = String.fromCharCode(97 + fileIndex) + (8 - rankIndex);
                    this.setPiece(squareName, char);
                    fileIndex++;
                } else {
                    // It's a number of empty squares
                    fileIndex += parseInt(char);
                }
            }
        });
    }
    
    setPiece(squareName, piece) {
        const square = this.getSquareElement(squareName);
        if (!square) return;
        
        // Remove existing piece
        const existingPiece = square.querySelector('.piece');
        if (existingPiece) {
            existingPiece.remove();
        }
        
        if (piece && piece !== ' ') {
            const pieceElement = document.createElement('div');
            pieceElement.className = 'piece';
            pieceElement.dataset.piece = piece;
            pieceElement.textContent = this.pieceSymbols[piece] || piece;
            pieceElement.draggable = this.options.draggable;
            
            square.appendChild(pieceElement);
        }
    }
    
    highlightSquare(squareName, className = 'highlighted') {
        const square = this.getSquareElement(squareName);
        if (square) {
            square.classList.add(className);
        }
    }
    
    highlightMove(fromSquare, toSquare) {
        this.clearHighlights();
        this.highlightSquare(fromSquare, 'last-move');
        this.highlightSquare(toSquare, 'last-move');
    }
    
    showCheck(kingSquare) {
        this.highlightSquare(kingSquare, 'check');
    }
    
    animateMove(fromSquare, toSquare, callback) {
        const fromElement = this.getSquareElement(fromSquare);
        const toElement = this.getSquareElement(toSquare);
        const piece = fromElement.querySelector('.piece');
        
        if (!piece) {
            if (callback) callback();
            return;
        }
        
        // Add animation class
        piece.classList.add('piece-move');
        
        setTimeout(() => {
            // Move the piece
            const capturedPiece = toElement.querySelector('.piece');
            if (capturedPiece) {
                capturedPiece.classList.add('piece-captured');
                setTimeout(() => capturedPiece.remove(), 400);
            }
            
            toElement.appendChild(piece);
            piece.classList.remove('piece-move');
            
            if (callback) callback();
        }, 150);
    }
    
    flip() {
        this.options.flipped = !this.options.flipped;
        this.board.classList.toggle('flipped');
    }
    
    getSquareElement(squareName) {
        return this.board.querySelector(`[data-square="${squareName}"]`);
    }
    
    resize(size) {
        this.options.size = size;
        this.board.style.width = `${size}px`;
        this.board.style.height = `${size}px`;
    }
    
    destroy() {
        this.container.innerHTML = '';
    }
    
    // Event handlers
    onMove(callback) {
        this.onMoveCallback = callback;
    }
    
    onSquareClick(callback) {
        this.onSquareClickCallback = callback;
    }
    
    onGetPossibleMoves(callback) {
        this.onGetPossibleMoves = callback;
    }
}

// Export for use in other modules
window.ChessBoard = ChessBoard;