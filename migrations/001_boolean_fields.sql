-- ==============================================
-- 迁移脚本：布尔语义字段类型规范化
-- 版本：V1.0
-- 日期：2026-06-02
-- 说明：将使用Integer存储的布尔语义字段统一为Boolean类型
-- ==============================================

-- SQLite 注意事项：
-- SQLite 中的 BOOLEAN 类型实际上是 INTEGER 的别名（0 = false, 1 = true）
-- 因此数据库层面不需要实际的类型转换，此脚本用于记录变更历史
-- 实际的修改将通过 ORM 模型更新实现

BEGIN TRANSACTION;

-- 验证现有数据格式（确保字段值为 0 或 1）
-- exams 表
UPDATE exams SET shuffle_question = 0 WHERE shuffle_question NOT IN (0, 1);
UPDATE exams SET shuffle_option = 0 WHERE shuffle_option NOT IN (0, 1);
UPDATE exams SET allow_early_submit = 1 WHERE allow_early_submit NOT IN (0, 1);

-- exam_sessions 表
UPDATE exam_sessions SET is_active = 1 WHERE is_active NOT IN (0, 1);

-- answers 表
UPDATE answers SET is_correct = 0 WHERE is_correct IS NOT NULL AND is_correct NOT IN (0, 1);
UPDATE answers SET is_flagged = 0 WHERE is_flagged NOT IN (0, 1);

-- 提交事务
COMMIT;

-- ==============================================
-- 变更记录
-- ==============================================
-- 1. exams.shuffle_question: Integer → Boolean
-- 2. exams.shuffle_option: Integer → Boolean  
-- 3. exams.allow_early_submit: Integer → Boolean
-- 4. exam_sessions.is_active: Integer → Boolean
-- 5. answers.is_correct: Integer → Boolean
-- 6. answers.is_flagged: Integer → Boolean

-- ==============================================
-- 验证查询
-- ==============================================
-- SELECT 'exams.shuffle_question' as field, COUNT(*) as count FROM exams WHERE shuffle_question NOT IN (0,1);
-- SELECT 'exams.shuffle_option' as field, COUNT(*) as count FROM exams WHERE shuffle_option NOT IN (0,1);
-- SELECT 'exams.allow_early_submit' as field, COUNT(*) as count FROM exams WHERE allow_early_submit NOT IN (0,1);
-- SELECT 'exam_sessions.is_active' as field, COUNT(*) as count FROM exam_sessions WHERE is_active NOT IN (0,1);
-- SELECT 'answers.is_correct' as field, COUNT(*) as count FROM answers WHERE is_correct IS NOT NULL AND is_correct NOT IN (0,1);
-- SELECT 'answers.is_flagged' as field, COUNT(*) as count FROM answers WHERE is_flagged NOT IN (0,1);