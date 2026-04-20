from dataclasses import dataclass, field
from threading import Lock
from typing import Dict, List, Tuple

from .flexlog import log_message
from .models import ProductEvaluation


@dataclass
class EvaluationCacheGroup:
    start_index: int
    end_index: int
    items: Dict[int, ProductEvaluation] = field(default_factory=dict)
    request_ranges: List[Tuple[int, int]] = field(default_factory=list)


class EvaluationCache:
    """
    Request-group cache for evaluated products.

    Groups cache by contiguous global index ranges derived from page/page_size math,
    supports partial request resolution, and enforces a global max-items limit.
    """

    def __init__(self, max_items: int = 100):
        self.max_items = max_items
        self._groups: List[EvaluationCacheGroup] = []
        self._lock = Lock()

    def resolve_request(self, start_index: int, count: int) -> Tuple[Dict[int, ProductEvaluation], List[int]]:
        """Return cached hits and missing indices for a request range."""
        if count <= 0:
            return {}, []

        hits: Dict[int, ProductEvaluation] = {}
        misses: List[int] = []

        with self._lock:
            for idx in range(start_index, start_index + count):
                cached = self._lookup_unlocked(idx)
                if cached is not None:
                    hits[idx] = cached
                else:
                    misses.append(idx)

        hit_rate = (len(hits) / count * 100) if count > 0 else 0
        log_message(
            f"[EvaluationCache] RESOLVE_REQUEST: range=[{start_index}..{start_index + count - 1}], "
            f"total={count}, hits={len(hits)}, misses={len(misses)}, hit_rate={hit_rate:.1f}%, groups={len(self._groups)}",
            additional_route="eval_cache_verbose",
        )
        log_message(
            f"[EvaluationCache] resolve_request start={start_index}, count={count}, hits={len(hits)}, misses={len(misses)}",
            additional_route="evaluation_cache",
        )
        return hits, misses

    def store_request_items(
        self,
        start_index: int,
        request_count: int,
        evaluated_items: Dict[int, ProductEvaluation],
    ) -> bool:
        """
        Cache an evaluated request.

        Tries to append/merge into an existing compatible group; otherwise creates
        a new group. If growth would exceed max_items, the new larger request is skipped.
        """
        if request_count <= 0 or not evaluated_items:
            log_message(
                f"[EvaluationCache] STORE_SKIP: invalid input (request_count={request_count}, items_count={len(evaluated_items)})",
                additional_route="eval_cache_verbose",
            )
            return False

        request_items = dict(evaluated_items)
        request_end = start_index + request_count - 1

        with self._lock:
            merge_candidates = self._find_merge_candidates_unlocked(start_index, request_end)
            current_total = self._total_items_unlocked()

            log_message(
                f"[EvaluationCache] STORE_START: range=[{start_index}..{request_end}], "
                f"items_to_store={len(request_items)}, current_total={current_total}, merge_candidates={len(merge_candidates)}",
                additional_route="eval_cache_verbose",
            )

            if merge_candidates:
                old_item_count = sum(len(self._groups[idx].items) for idx in merge_candidates)
                merged_items: Dict[int, ProductEvaluation] = {}
                merged_start = start_index
                merged_end = request_end
                merged_ranges: List[Tuple[int, int]] = []

                for idx in merge_candidates:
                    group = self._groups[idx]
                    merged_items.update(group.items)
                    merged_start = min(merged_start, group.start_index)
                    merged_end = max(merged_end, group.end_index)
                    merged_ranges.extend(group.request_ranges)

                merged_items.update(request_items)
                merged_ranges.append((start_index, request_count))

                new_item_count = len(merged_items)
                projected_total = current_total - old_item_count + new_item_count
                adds_new_items = new_item_count > old_item_count
                net_new_items = new_item_count - old_item_count

                log_message(
                    f"[EvaluationCache] MERGE_DECISION: candidates={len(merge_candidates)}, "
                    f"old_items={old_item_count}, new_items={new_item_count}, "
                    f"net_new={net_new_items}, projected_total={projected_total}, max={self.max_items}",
                    additional_route="eval_cache_verbose",
                )

                if projected_total > self.max_items and adds_new_items:
                    log_message(
                        f"[EvaluationCache] STORE_REJECT_MERGE: projected_total={projected_total} > max_items={self.max_items}, skipping merge",
                        additional_route="eval_cache_verbose",
                    )
                    log_message(
                        f"[EvaluationCache] Skipped merged cache write (projected_total={projected_total} > max_items={self.max_items})",
                        additional_route="evaluation_cache",
                    )
                    return False

                merged_group = EvaluationCacheGroup(
                    start_index=merged_start,
                    end_index=merged_end,
                    items=merged_items,
                    request_ranges=merged_ranges,
                )

                for idx in sorted(merge_candidates, reverse=True):
                    del self._groups[idx]

                self._groups.append(merged_group)
                self._groups.sort(key=lambda group: group.start_index)

                final_total = self._total_items_unlocked()
                log_message(
                    f"[EvaluationCache] STORE_MERGE_SUCCESS: merged_range=[{merged_start}..{merged_end}], "
                    f"final_items={new_item_count}, total_cached={final_total}, groups={len(self._groups)}",
                    additional_route="eval_cache_verbose",
                )
                log_message(
                    f"[EvaluationCache] Updated merged group range={merged_start}-{merged_end}, total_cached_items={final_total}",
                    additional_route="evaluation_cache",
                )
                return True

            request_item_count = len(request_items)
            projected_total = current_total + request_item_count

            log_message(
                f"[EvaluationCache] NEW_GROUP_DECISION: no_merge_candidates, "
                f"current_total={current_total}, items_to_add={request_item_count}, projected_total={projected_total}, max={self.max_items}",
                additional_route="eval_cache_verbose",
            )

            if projected_total > self.max_items:
                log_message(
                    f"[EvaluationCache] STORE_REJECT_NEW: projected_total={projected_total} > max_items={self.max_items}, skipping new group",
                    additional_route="eval_cache_verbose",
                )
                log_message(
                    f"[EvaluationCache] Skipped new group cache write (projected_total={projected_total} > max_items={self.max_items})",
                    additional_route="evaluation_cache",
                )
                return False

            new_group = EvaluationCacheGroup(
                start_index=start_index,
                end_index=request_end,
                items=request_items,
                request_ranges=[(start_index, request_count)],
            )
            self._groups.append(new_group)
            self._groups.sort(key=lambda group: group.start_index)

            final_total = self._total_items_unlocked()
            log_message(
                f"[EvaluationCache] STORE_NEW_SUCCESS: new_range=[{start_index}..{request_end}], "
                f"items={request_item_count}, total_cached={final_total}, groups={len(self._groups)}",
                additional_route="eval_cache_verbose",
            )
            log_message(
                f"[EvaluationCache] Added new group range={start_index}-{request_end}, total_cached_items={final_total}",
                additional_route="evaluation_cache",
            )
            return True

    def total_cached_items(self) -> int:
        with self._lock:
            return self._total_items_unlocked()

    def total_groups(self) -> int:
        with self._lock:
            return len(self._groups)

    def _lookup_unlocked(self, index: int) -> ProductEvaluation | None:
        for group in self._groups:
            if group.start_index <= index <= group.end_index:
                cached = group.items.get(index)
                if cached is not None:
                    return cached
        return None

    def _find_merge_candidates_unlocked(self, start_index: int, end_index: int) -> List[int]:
        candidates: List[int] = []
        for idx, group in enumerate(self._groups):
            disjoint = group.end_index < (start_index - 1) or group.start_index > (end_index + 1)
            if not disjoint:
                candidates.append(idx)
        
        if candidates:
            candidate_ranges = ", ".join(
                f"[{self._groups[idx].start_index}..{self._groups[idx].end_index}]"
                for idx in candidates
            )
            log_message(
                f"[EvaluationCache] MERGE_CANDIDATES_FOUND: query_range=[{start_index}..{end_index}], "
                f"candidates={len(candidates)}, ranges={candidate_ranges}",
                additional_route="eval_cache_verbose",
            )
        
        return candidates

    def _total_items_unlocked(self) -> int:
        return sum(len(group.items) for group in self._groups)
