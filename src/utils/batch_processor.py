#!/usr/bin/env python3
"""
Internal batch processing utility for FPT University Agent
This is for internal operations, testing, and admin tools only.
NOT for public API usage.
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add src to Python path
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from api.factories.service_factory import ServiceFactory  # noqa: E402


class BatchProcessor:
    """Internal batch processor for multiple queries"""

    def __init__(self):
        self.service_factory = ServiceFactory()
        self.intent_service = None

    async def initialize(
        self, model_id: str = "gpt-4o", debug_mode: bool = False
    ) -> bool:
        """Initialize the batch processor"""
        success = await self.service_factory.initialize_services(
            model_id=model_id, debug_mode=debug_mode
        )

        if success:
            self.intent_service = self.service_factory.get_intent_service()

        return success and self.intent_service is not None

    async def process_queries(
        self,
        queries: List[str],
        max_concurrent: int = 10,
        include_metadata: bool = True,
    ) -> Dict[str, Any]:
        """
        Process multiple queries and return structured results

        Args:
            queries: List of query strings
            max_concurrent: Maximum concurrent operations
            include_metadata: Whether to include detailed metadata

        Returns:
            Dictionary with results and performance metrics
        """
        if not self.intent_service:
            raise RuntimeError("Batch processor not initialized")

        start_time = time.time()

        # Process queries
        results = await self.intent_service.detect_batch_queries(
            queries=queries, max_concurrent=max_concurrent
        )

        processing_time = (time.time() - start_time) * 1000

        # Format results
        formatted_results = []
        high_confidence_count = 0

        for i, (query, result) in enumerate(zip(queries, results)):
            formatted_result = {
                "index": i,
                "query": query,
                "intent_id": result.id,
                "confidence": result.confidence,
                "method": result.method.value,
                "timestamp": result.timestamp.isoformat(),
            }

            if include_metadata:
                formatted_result["metadata"] = result.metadata
                formatted_result["confidence_level"] = result.confidence_level.value

            if result.confidence >= 0.7:
                high_confidence_count += 1

            formatted_results.append(formatted_result)

        # Calculate metrics
        total_queries = len(queries)
        success_rate = (
            (high_confidence_count / total_queries) * 100 if total_queries > 0 else 0
        )
        avg_processing_time = (
            processing_time / total_queries if total_queries > 0 else 0
        )

        return {
            "results": formatted_results,
            "metrics": {
                "total_queries": total_queries,
                "high_confidence_count": high_confidence_count,
                "success_rate": success_rate,
                "processing_time_ms": processing_time,
                "avg_processing_time_ms": avg_processing_time,
                "max_concurrent": max_concurrent,
            },
        }

    async def process_from_file(
        self,
        file_path: str,
        max_concurrent: int = 10,
        output_file: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process queries from a file

        Args:
            file_path: Path to file containing queries (one per line)
            max_concurrent: Maximum concurrent operations
            output_file: Optional output file for results

        Returns:
            Processing results
        """
        # Read queries from file
        queries = []
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                query = line.strip()
                if query and not query.startswith("#"):  # Skip empty lines and comments
                    queries.append(query)

        if not queries:
            raise ValueError(f"No valid queries found in {file_path}")

        print(f"📝 Processing {len(queries)} queries from {file_path}")

        # Process queries
        results = await self.process_queries(
            queries=queries, max_concurrent=max_concurrent, include_metadata=True
        )

        # Save to output file if specified
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"💾 Results saved to {output_file}")

        return results

    def print_summary(self, results: Dict[str, Any]) -> None:
        """Print a summary of batch processing results"""
        metrics = results["metrics"]

        print("\n📊 Batch Processing Summary:")
        print(f"   Total queries: {metrics['total_queries']}")
        print(f"   High confidence (≥0.7): {metrics['high_confidence_count']}")
        print(f"   Success rate: {metrics['success_rate']:.1f}%")
        print(f"   Processing time: {metrics['processing_time_ms']:.1f}ms")
        print(f"   Average per query: {metrics['avg_processing_time_ms']:.1f}ms")
        print(f"   Max concurrent: {metrics['max_concurrent']}")

        # Intent distribution
        intent_counts: Dict[str, int] = {}
        for result in results["results"]:
            intent_id = result["intent_id"]
            intent_counts[intent_id] = intent_counts.get(intent_id, 0) + 1

        print("\n🎯 Intent Distribution:")
        for intent_id, count in sorted(
            intent_counts.items(), key=lambda x: x[1], reverse=True
        ):
            percentage = (count / metrics["total_queries"]) * 100
            print(f"   {intent_id}: {count} ({percentage:.1f}%)")


async def main():
    """Main function for command line usage"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Internal batch processor for FPT University Agent"
    )
    parser.add_argument("--file", "-f", help="Input file with queries (one per line)")
    parser.add_argument("--queries", "-q", nargs="+", help="Direct queries to process")
    parser.add_argument("--output", "-o", help="Output file for results (JSON)")
    parser.add_argument(
        "--concurrent",
        "-c",
        type=int,
        default=10,
        help="Max concurrent operations (1-20)",
    )
    parser.add_argument("--model", "-m", default="gpt-4o", help="Model ID to use")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    if not args.file and not args.queries:
        parser.error("Either --file or --queries must be specified")

    if args.concurrent < 1 or args.concurrent > 20:
        parser.error("Concurrent operations must be between 1 and 20")

    # Initialize processor
    processor = BatchProcessor()
    print("🚀 Initializing batch processor...")

    success = await processor.initialize(model_id=args.model, debug_mode=args.debug)
    if not success:
        print("❌ Failed to initialize batch processor")
        return 1

    print("✅ Batch processor initialized")

    try:
        if args.file:
            # Process from file
            results = await processor.process_from_file(
                file_path=args.file,
                max_concurrent=args.concurrent,
                output_file=args.output,
            )
        else:
            # Process direct queries
            results = await processor.process_queries(
                queries=args.queries,
                max_concurrent=args.concurrent,
                include_metadata=True,
            )

            # Save to output file if specified
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                print(f"💾 Results saved to {args.output}")

        # Print summary
        processor.print_summary(results)

        return 0

    except Exception as e:
        print(f"❌ Error during batch processing: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
