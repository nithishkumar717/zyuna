const { DataTypes } = require('sequelize');
const sequelize = require('../sequelize');
const BaseModel = require('../BaseModel');

const settingsCache = new Map();

class AutoplaySetting extends BaseModel {
    static init(sequelize) {
        super.init(
            {
                id: { type: DataTypes.INTEGER, primaryKey: true, autoIncrement: true },
                guildId: { type: DataTypes.STRING, allowNull: false, unique: true },
                enabled: { type: DataTypes.BOOLEAN, allowNull: false, defaultValue: false },
                language: { type: DataTypes.STRING, allowNull: false, defaultValue: 'auto' },
            },
            {
                sequelize,
                modelName: 'AutoplaySetting',
                tableName: 'autoplay_settings',
                timestamps: true,
            }
        );

        return this;
    }

    static async getGuildSetting(guildId) {
        const key = String(guildId);
        if (settingsCache.has(key)) {
            return settingsCache.get(key);
        }

        try {
            const record = await this.findOne({ where: { guildId: key } });
            const setting = {
                enabled: record ? Boolean(record.enabled) : false,
                language: record ? String(record.language || 'auto').toLowerCase() : 'auto',
            };
            settingsCache.set(key, setting);
            return setting;
        } catch {
            return { enabled: false, language: 'auto' };
        }
    }

    static async setGuildSetting(guildId, updates = {}) {
        const key = String(guildId);
        const current = await this.getGuildSetting(key);
        const next = {
            enabled: updates.enabled !== undefined ? Boolean(updates.enabled) : current.enabled,
            language: updates.language !== undefined ? String(updates.language).toLowerCase() : current.language,
        };

        settingsCache.set(key, next);

        try {
            const [record, created] = await this.findOrCreate({
                where: { guildId: key },
                defaults: { guildId: key, ...next },
            });
            if (!created) {
                await record.update(next);
            }
        } catch {
            // Keep in-memory cache even if SQLite write is temporarily busy
        }

        return next;
    }
}

AutoplaySetting.init(sequelize);

module.exports = AutoplaySetting;
