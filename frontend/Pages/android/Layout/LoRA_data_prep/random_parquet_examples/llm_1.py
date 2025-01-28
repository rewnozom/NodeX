from pathlib import Path
import pandas as pd
import json
from typing import Dict, List, Union, Optional, Tuple
import logging
from dataclasses import dataclass
import pyarrow as pa
import pyarrow.parquet as pq
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, track
from rich import print as rprint
from rich.table import Table
from rich.syntax import Syntax
import shutil
import sys
import matplotlib.pyplot as plt
import seaborn as sns
from io import StringIO
import re
import hashlib
import numpy as np
from datetime import datetime
import tiktoken

console = Console()

@dataclass
class DirectoryConfig:
    """Konfiguration för mappar."""
    raw_dir: Path = Path("./raw_data")
    processed_dir: Path = Path("./processed")
    view_dir: Path = Path("./view")
    training_dir: Path = Path("./training")
    temp_dir: Path = Path("./temp")
    archive_dir: Path = Path("./archive")

@dataclass
class ProcessingConfig:
    """Konfiguration för dataprocessning."""
    required_columns: List[str] = None
    supported_file_types: List[str] = None
    min_code_length: int = 10
    max_code_length: int = 100000

class TokenCounter:
    """Hanterar token-räkning för träningsdata."""
    
    def __init__(self, encoding_name: str = "cl100k_base"):
        self.encoding = tiktoken.get_encoding(encoding_name)
        self.min_tokens = 50
        self.max_tokens = 131072
    
    def count_tokens(self, text: str) -> int:
        """Räknar tokens i en text."""
        return len(self.encoding.encode(text))
    
    def validate_token_count(self, text: str) -> Tuple[bool, str, int]:
        """Validerar att texten har rätt antal tokens."""
        token_count = self.count_tokens(text)
        
        if token_count < self.min_tokens:
            return False, f"För få tokens ({token_count}), minimum är {self.min_tokens}", token_count
        if token_count > self.max_tokens:
            return False, f"För många tokens ({token_count}), maximum är {self.max_tokens}", token_count
        
        return True, "OK", token_count

class DataValidator:
    """Validerar data."""
    
    def __init__(self, config: ProcessingConfig):
        self.config = config
    
    def validate_content(self, content: str) -> tuple[bool, str]:
        """Validerar kodinnehåll."""
        if not content or not isinstance(content, str):
            return False, "Empty or invalid content"
        if len(content) < self.config.min_code_length:
            return False, f"Content too short (min {self.config.min_code_length} chars)"
        if len(content) > self.config.max_code_length:
            return False, f"Content too long (max {self.config.max_code_length} chars)"
        return True, "OK"
    
    def validate_file_type(self, filename: str) -> tuple[bool, str]:
        """Validerar filtyp."""
        suffix = Path(filename).suffix
        if not self.config.supported_file_types:
            return True, "OK"
        if suffix not in self.config.supported_file_types:
            return False, f"Unsupported file type: {suffix}"
        return True, "OK"

class DataProcessor:
    """Processar och organiserar data."""
    
    def __init__(self, dir_config: DirectoryConfig, proc_config: ProcessingConfig):
        self.dir_config = dir_config
        self.proc_config = proc_config
        self.validator = DataValidator(proc_config)
        self.token_counter = TokenCounter()
        self._setup_directories()
        
    def _setup_directories(self):
        """Skapar alla nödvändiga mappar."""
        for directory in [self.dir_config.raw_dir, 
                         self.dir_config.processed_dir,
                         self.dir_config.view_dir,
                         self.dir_config.training_dir,
                         self.dir_config.temp_dir,
                         self.dir_config.archive_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def process_file(self, file_path: Path) -> Optional[Dict]:
        """Processar en fil med token-validering."""
        try:
            # Validera filtyp
            valid, msg = self.validator.validate_file_type(file_path.name)
            if not valid:
                console.print(f"[yellow]{msg}[/]")
                return None
            
            # Läs innehåll
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Validera innehåll
            valid, msg = self.validator.validate_content(content)
            if not valid:
                console.print(f"[yellow]{file_path.name}: {msg}[/]")
                return None
            
            # Validera tokens
            valid, msg, token_count = self.token_counter.validate_token_count(content)
            if not valid:
                console.print(f"[yellow]{file_path.name}: {msg}[/]")
                return None
            
            return {
                'filename': file_path.name,
                'content': content,
                'language': file_path.suffix.lstrip('.'),
                'type': 'code',
                'tokens': token_count,
                'processed_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            console.print(f"[red]Error processing {file_path}: {str(e)}[/]")
            return None
    
    def process_directory(self) -> pd.DataFrame:
        """Processar alla filer i raw-mappen."""
        processed_data = []
        
        for file_path in track(list(self.dir_config.raw_dir.glob("*")), 
                             description="Processing files..."):
            if file_path.is_file():
                data = self.process_file(file_path)
                if data:
                    processed_data.append(data)
                    # Flytta till processed
                    shutil.move(str(file_path), 
                              str(self.dir_config.processed_dir / file_path.name))
        
        if not processed_data:
            raise ValueError("No valid files found to process")
            
        return pd.DataFrame(processed_data)
    
    def save_processed_data(self, df: pd.DataFrame) -> Dict[str, Path]:
        """Sparar processad data i alla format."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Spara för träning (parquet)
        training_file = self.dir_config.training_dir / f"training_data_{timestamp}.parquet"
        df.to_parquet(training_file, index=False)
        
        # Spara för viewing (csv)
        csv_file = self.dir_config.view_dir / f"data_{timestamp}.csv"
        df.to_csv(csv_file, index=False)
        
        # Skapa markdown preview
        self._create_markdown_preview(df, timestamp)
        
        return {
            'training': training_file,
            'csv': csv_file,
            'markdown': self.dir_config.view_dir / f"preview_{timestamp}.md"
        }
    
    def _create_markdown_preview(self, df: pd.DataFrame, timestamp: str):
        """Skapar markdown preview med token-info."""
        markdown_file = self.dir_config.view_dir / f"preview_{timestamp}.md"
        
        with open(markdown_file, 'w', encoding='utf-8') as f:
            f.write("# Processed Code Files\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Statistik
            f.write("## Statistics\n\n")
            f.write(f"Total files: {len(df)}\n")
            if 'tokens' in df.columns:
                f.write(f"Total tokens: {df['tokens'].sum():,}\n")
                f.write(f"Average tokens per file: {df['tokens'].mean():.1f}\n")
            if 'language' in df.columns:
                f.write("\nLanguage distribution:\n")
                for lang, count in df['language'].value_counts().items():
                    f.write(f"- {lang}: {count}\n")
            f.write("\n---\n\n")
            
            # Kodinnehåll
            for _, row in df.iterrows():
                f.write(f"## {row['filename']}\n")
                f.write(f"Language: {row['language']}\n")
                f.write(f"Tokens: {row['tokens']:,}\n\n")
                f.write("```" + row['language'] + "\n")
                f.write(row['content'])
                f.write("\n```\n\n")
                f.write("---\n\n")

class DataAnalyzer:
    """Analyserar träningsdata."""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        
    def get_basic_stats(self) -> Dict:
        """Returnerar grundläggande statistik inklusive token-info."""
        stats = {
            'total_rows': len(self.df),
            'duplicates': self.df.duplicated().sum(),
            'empty_values': self.df.isna().sum().to_dict(),
            'memory_usage': self.df.memory_usage(deep=True).sum() / 1024**2,  # MB
        }
        
        if 'content' in self.df.columns:
            stats['avg_content_length'] = self.df['content'].str.len().mean()
            stats['max_content_length'] = self.df['content'].str.len().max()
        
        if 'tokens' in self.df.columns:
            stats['total_tokens'] = self.df['tokens'].sum()
            stats['avg_tokens'] = self.df['tokens'].mean()
            stats['min_tokens'] = self.df['tokens'].min()
            stats['max_tokens'] = self.df['tokens'].max()
            
        return stats
    
    def find_similar_content(self, threshold: float = 0.9) -> List[tuple]:
        """Hittar liknande kodinnehåll."""
        similar_pairs = []
        contents = self.df['content'].tolist()
        
        for i in range(len(contents)):
            for j in range(i + 1, len(contents)):
                similarity = self._calculate_similarity(contents[i], contents[j])
                if similarity > threshold:
                    similar_pairs.append((i, j, similarity))
                    
        return similar_pairs
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Beräknar textlikhet."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0
    
    def generate_visualizations(self, output_dir: Path):
        """Skapar visualiseringar inklusive token-distribution."""
        plt.style.use('seaborn')
        
        # Innehållslängd distribution
        plt.figure(figsize=(12, 6))
        sns.histplot(self.df['content'].str.len(), bins=50)
        plt.title('Distribution of Code Lengths')
        plt.xlabel('Length (characters)')
        plt.ylabel('Count')
        plt.savefig(output_dir / 'code_lengths.png')
        plt.close()
        
        # Språkfördelning om det finns
        if 'language' in self.df.columns:
            plt.figure(figsize=(10, 6))
            self.df['language'].value_counts().plot(kind='bar')
            plt.title('Programming Language Distribution')
            plt.xlabel('Language')
            plt.ylabel('Count')
            plt.tight_layout()
            plt.savefig(output_dir / 'language_distribution.png')
            plt.close()
        
        # Token distribution
        if 'tokens' in self.df.columns:
            plt.figure(figsize=(12, 6))
            sns.histplot(self.df['tokens'], bins=50)
            plt.title('Distribution of Token Counts')
            plt.xlabel('Number of Tokens')
            plt.ylabel('Count')
            plt.savefig(output_dir / 'token_distribution.png')
            plt.close()

class Menu:
    """Hanterar programmets meny och användarinteraktion."""
    
    def __init__(self, processor: DataProcessor):
        self.processor = processor
        
    def display_main_menu(self):
        """Visar huvudmenyn."""
        while True:
            console.clear()
            console.print(Panel.fit(
                "[bold blue]LLM Training Data Processor[/]\n\n"
                "1. Process All Files (Auto Mode)\n"
                "2. Analyze Existing Data\n"
                "3. View Directory Contents\n"
                "4. Clean Up Directories\n"
                "5. Exit",
                title="Main Menu"
            ))
            
            choice = Prompt.ask("Select an option", choices=["1", "2", "3", "4", "5"])
            
            if choice == "1":
                self.process_auto_mode()
            elif choice == "2":
                self.analyze_data()
            elif choice == "3":
                self.view_directories()
            elif choice == "4":
                self.cleanup_directories()
            elif choice == "5":
                console.print("[yellow]Exiting program...[/]")
                sys.exit()
    
    def process_auto_mode(self):
        """Kör automatisk processning."""
        try:
            # Processa filer
            df = self.processor.process_directory()
            
            # Spara i alla format
            saved_files = self.processor.save_processed_data(df)
            
            # Visa resultat
            console.print("[bold green]Processing complete![/]")
            console.print(f"\nProcessed {len(df)} files:")
            console.print(f"Training data: {saved_files['training']}")
            console.print(f"CSV view: {saved_files['csv']}")
            console.print(f"Markdown preview: {saved_files['markdown']}")
            
            # Analysera
            analyzer = DataAnalyzer(df)
            stats = analyzer.get_basic_stats()
            
            table = Table(title="Data Analysis")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="magenta")
            
            for key, value in stats.items():
                table.add_row(key, str(value))
                
            console.print(table)
            
            # Generera visualiseringar
            if Confirm.ask("Generate visualizations?"):
                analyzer.generate_visualizations(self.processor.dir_config.view_dir)
                console.print("[green]Visualizations saved![/]")
            
        except Exception as e:
            console.print(f"[bold red]Error: {str(e)}[/]")
        
        input("\nPress Enter to continue...")
    
    def analyze_data(self):
        """Analyserar existerande data."""
        try:
            # Leta efter senaste training data
            training_files = list(self.processor.dir_config.training_dir.glob("*.parquet"))
            if not training_files:
                console.print("[yellow]No training data found[/]")
                return
            
            latest_file = max(training_files, key=lambda p: p.stat().st_mtime)
            df = pd.read_parquet(latest_file)
            
            analyzer = DataAnalyzer(df)
            
            # Visa statistik
            stats = analyzer.get_basic_stats()
            table = Table(title=f"Analysis of {latest_file.name}")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="magenta")
            
            for key, value in stats.items():
                table.add_row(key, str(value))
                
            console.print(table)
            
            # Visa liknande innehåll
            similar = analyzer.find_similar_content(threshold=0.9)
            if similar:
                console.print("\n[yellow]Found similar content:[/]")
                for i, j, sim in similar[:5]:
                    console.print(f"\nSimilarity: {sim:.2f}")
                    console.print(f"1: {df.iloc[i]['filename']}")
                    console.print(f"2: {df.iloc[j]['filename']}")
            
            # Generera visualiseringar
            if Confirm.ask("\nGenerate new visualizations?"):
                analyzer.generate_visualizations(self.processor.dir_config.view_dir)
                console.print("[green]Visualizations saved![/]")
            
        except Exception as e:
            console.print(f"[bold red]Error during analysis: {str(e)}[/]")
        
        input("\nPress Enter to continue...")
    
    def view_directories(self):
        """Visar innehåll i alla mappar."""
        dirs = {
            "Raw": self.processor.dir_config.raw_dir,
            "Processed": self.processor.dir_config.processed_dir,
            "Training": self.processor.dir_config.training_dir,
            "View": self.processor.dir_config.view_dir,
            "Archive": self.processor.dir_config.archive_dir
        }
        
        for name, directory in dirs.items():
            console.print(f"\n[bold blue]{name} Directory Contents:[/]")
            files = list(directory.glob("**/*"))
            if not files:
                console.print("[yellow]Empty[/]")
            else:
                for file in files:
                    if file.is_file():
                        size = file.stat().st_size / 1024  # KB
                        modified = datetime.fromtimestamp(file.stat().st_mtime)
                        console.print(
                            f"- {file.name} "
                            f"({size:.1f}KB, "
                            f"modified: {modified.strftime('%Y-%m-%d %H:%M:%S')})"
                        )
        
        input("\nPress Enter to continue...")
    
    def cleanup_directories(self):
        """Rensar mappar."""
        console.print("\n[bold]Select directory to clean:[/]")
        console.print("1. Processed files")
        console.print("2. View files")
        console.print("3. Training files")
        console.print("4. Archive")
        console.print("5. All directories")
        console.print("6. Back to main menu")
        
        choice = Prompt.ask("Select option", choices=["1", "2", "3", "4", "5", "6"])
        
        if choice == "6":
            return
            
        try:
            if choice == "1" or choice == "5":
                shutil.rmtree(self.processor.dir_config.processed_dir)
                self.processor.dir_config.processed_dir.mkdir()
                console.print("[green]Processed directory cleared![/]")
                
            if choice == "2" or choice == "5":
                shutil.rmtree(self.processor.dir_config.view_dir)
                self.processor.dir_config.view_dir.mkdir()
                console.print("[green]View directory cleared![/]")
                
            if choice == "3" or choice == "5":
                if Confirm.ask("Are you sure you want to delete all training data?"):
                    shutil.rmtree(self.processor.dir_config.training_dir)
                    self.processor.dir_config.training_dir.mkdir()
                    console.print("[green]Training directory cleared![/]")
                
            if choice == "4" or choice == "5":
                if Confirm.ask("Are you sure you want to clear the archive?"):
                    shutil.rmtree(self.processor.dir_config.archive_dir)
                    self.processor.dir_config.archive_dir.mkdir()
                    console.print("[green]Archive cleared![/]")
                    
        except Exception as e:
            console.print(f"[bold red]Error during cleanup: {str(e)}[/]")
        
        input("\nPress Enter to continue...")

def main():
    # Standardkonfiguration
    dir_config = DirectoryConfig(
        raw_dir=Path("./raw_data"),
        processed_dir=Path("./processed"),
        view_dir=Path("./view"),
        training_dir=Path("./training"),
        temp_dir=Path("./temp"),
        archive_dir=Path("./archive")
    )
    
    proc_config = ProcessingConfig(
        supported_file_types=['.py', '.ts', '.tsx', '.jsx', '.js'],
        min_code_length=10,
        max_code_length=100000
    )
    
    # Skapa processor och meny
    processor = DataProcessor(dir_config, proc_config)
    menu = Menu(processor)
    
    # Visa välkomstmeddelande
    console.print("[bold blue]LLM Training Data Processor[/]")
    console.print("\nDirectory structure:")
    for name, path in {
        "Raw data": dir_config.raw_dir,
        "Processed": dir_config.processed_dir,
        "View": dir_config.view_dir,
        "Training": dir_config.training_dir,
        "Archive": dir_config.archive_dir
    }.items():
        console.print(f"{name}: {path}")
    
    input("\nPress Enter to continue...")
    
    try:
        menu.display_main_menu()
    except KeyboardInterrupt:
        console.print("\n[yellow]Program terminated by user.[/]")
    except Exception as e:
        console.print(f"\n[bold red]Unexpected error: {str(e)}[/]")
        raise

if __name__ == "__main__":
    main()
